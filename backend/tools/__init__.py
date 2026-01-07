from typing import Optional
from .math_tools import add_numbers, multiply_numbers, subtract_numbers, divide_numbers
from .agent_tools import final_answer
from .rag_tools import get_retriever_tool


def get_all_tools(rag_documents_path: Optional[str] = None, rag_description: Optional[str] = None):
    tool_list = [
        add_numbers,
        multiply_numbers,
        subtract_numbers,
        divide_numbers,
    ]

    if rag_documents_path:
        rag_tool = get_retriever_tool(rag_documents_path, description=rag_description)
        if rag_tool:
            tool_list.append(rag_tool)

    #tool_list.append(final_answer) # Uncomment if your agent supports forced tool usage
    return tool_list

__all__ = [
    "get_all_tools",
    "get_tool_mapping",
    "add_numbers",
    "multiply_numbers",
    "subtract_numbers",
    "divide_numbers",
    "final_answer",
    "get_retriever_tool",
]
