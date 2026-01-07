from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, SystemMessagePromptTemplate, HumanMessagePromptTemplate
import asyncio
from langchain_core.callbacks.base import AsyncCallbackHandler
from langchain_core.runnables.base import RunnableSerializable
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
import json
from tools import get_all_tools
from middleware import ModelFallbackMiddleware

load_dotenv()



model_middleware = ModelFallbackMiddleware(
    primary_model_name="qwen/qwen3-32b",
    backup_model_name="openai/gpt-oss-20b",
    temperature=0.0
)

llm = model_middleware.get_model()


system_prompt = "You are Beacon, a helpful intelligent AI assistant" 

prompt_template = ChatPromptTemplate.from_messages([
  SystemMessagePromptTemplate.from_template(system_prompt),
  MessagesPlaceholder(variable_name="chat_history"),
  HumanMessagePromptTemplate.from_template("{input}"),
  MessagesPlaceholder(variable_name="agent_scratchpad"),
])

class QueueCallbackHandler(AsyncCallbackHandler):
    def __init__(self, queue: asyncio.Queue):
        self.queue = queue
        self.final_answer_seen = False

    async def __aiter__(self):
        while True:
          if self.queue.empty():
            await asyncio.sleep(0.1)
            continue
          token_or_done = await self.queue.get()

          if token_or_done in ("<<DONE>>", "<<STEP_END>>"):
            if token_or_done == "<<STEP_END>>":
              yield token_or_done
            return
          
          if token_or_done:
            yield token_or_done

    async def on_llm_new_token(self, *args, **kwargs) -> None:
      chunk = kwargs.get("chunk")
      if chunk:
        if tool_calls := chunk.message.additional_kwargs.get("tool_calls"):
          if tool_calls[0]["function"]["name"] == "final_answer":
            self.final_answer_seen = True
      await self.queue.put(chunk)
      return

    async def on_llm_end(self, *args, **kwargs) -> None:
      if self.final_answer_seen:
        await self.queue.put("<<DONE>>")
      else:
        await self.queue.put("<<STEP_END>>")
      return


class CustomAgentExecutor:
  chat_history: list[BaseMessage]

  def __init__(
    self,
    max_iterations: int = 3,
    chat_history: list[BaseMessage] = None,
    rag_documents_path: str | None = None,
    rag_description: str | None = None,
  ):
    self.chat_history = chat_history if chat_history else []
    self.max_iterations = max_iterations

    self.tools = get_all_tools(rag_documents_path, rag_description)
    self.name2tool = {tool.name: tool.func for tool in self.tools}

    self.agent: RunnableSerializable = (
      {
        "input": lambda x: x["input"],
        "chat_history": lambda x: x["chat_history"],
        "agent_scratchpad": lambda x: x.get("agent_scratchpad", [])
      }
      | prompt_template
      | llm.bind_tools(self.tools, tool_choice="auto") 
    )

  async def invoke(self, input: str, streamer: QueueCallbackHandler, verbose: bool = False) -> dict:
      count = 0
      agent_scratchpad = []
      tools_used_in_session = []
      while count < self.max_iterations:
          async def stream(query: str):
            response = self.agent.with_config(callbacks=[streamer])
            output = None
            async for token in response.astream({
                "input": query,
                "chat_history": self.chat_history,
                "agent_scratchpad": agent_scratchpad
            }):
              if output is None:
                output = token
              else:
                output += token

              if token.content != "":
                if verbose:
                  print(f"Content: {token.content}", end='', flush=True)
              tool_calls = token.additional_kwargs.get("tool_calls")
              if tool_calls:
                if verbose:
                  print(f"tool_calls: {tool_calls}\n", flush=True)
                  tool_name = tool_calls[0]["function"]["name"]
                  if tool_name:
                    print(f"tool_name: {tool_name}\n", flush=True)
                  arg = tool_calls[0]["function"]["arguments"]
                  if arg != "":
                    print(f"arg: {arg}\n", flush=True)
            
            return AIMessage(
              content=output.content,
              tool_calls=output.tool_calls,
            )
          
          tool_call = await stream(query=input)
          if len(tool_call.tool_calls) > 0:
            for tool_used in tool_call.tool_calls:
              tool_name = tool_used["name"]
              # uncomment if your agent supports forced tool usage
              # if tool_name == "final_answer":
              #   final_answer = tool_used["args"]
              #   final_answer_str = json.dumps(final_answer)
              #   self.chat_history.extend([
              #       HumanMessage(content=input),
              #       AIMessage(content=final_answer_str)
              #   ])
              #   return {final_answer}
              tools_used_in_session.append(tool_name)
              agent_scratchpad.append(tool_call)
              tool_args = tool_used["args"]
              tool_call_id = tool_used["id"]
              tool_out = self.name2tool[tool_name](**tool_args)

              tool_exec = ToolMessage(
                  content=f"{tool_out}",
                  tool_call_id=tool_call_id
              )
              agent_scratchpad.append(tool_exec)
              
          else:
            tool_out = tool_call.content
            self.chat_history.extend([
                HumanMessage(content=input),
                AIMessage(content=tool_out)
            ])
            return {"answer": tool_out, "tools_used": tools_used_in_session}
              
          count += 1
                
      return {"answer": "Maximum iterations reached without a final answer.", "tools_used": tools_used_in_session}
