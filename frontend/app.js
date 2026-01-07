const API_BASE = "http://localhost:8000";
const apiBaseEl = document.getElementById("api-base");
apiBaseEl.textContent = API_BASE;

const sessionsEl = document.getElementById("sessions");
const createSessionBtn = document.getElementById("create-session");
const deleteSessionBtn = document.getElementById("delete-session");
const sessionMetaEl = document.getElementById("session-meta");
const ragPathInput = document.getElementById("rag-path");
const ragDescriptionInput = document.getElementById("rag-description");
const createModal = document.getElementById("create-modal");
const createCloseBtn = document.getElementById("create-close");
const createCancelBtn = document.getElementById("create-cancel");
const createForm = document.getElementById("create-form");
const createSessionNameInput = document.getElementById("create-session-name");
const createRagPathInput = document.getElementById("create-rag-path");
const createRagDescriptionInput = document.getElementById("create-rag-description");
const createSubmitBtn = document.getElementById("create-submit");
const enableRagBtn = document.getElementById("enable-rag");
const ragStatusEl = document.getElementById("rag-status");
const messagesEl = document.getElementById("messages");
const welcomeStateEl = document.getElementById("welcome-state");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const messageTemplate = document.getElementById("message-template");

let currentSessionId = null;
let streaming = false;
let currentStreamEl = null;
let currentStreamMeta = null;

function toggleWelcomeState(show) {
  if (show) {
    welcomeStateEl.style.display = "flex";
    messagesEl.style.display = "none";
    chatForm.style.display = "none";
  } else {
    welcomeStateEl.style.display = "none";
    messagesEl.style.display = "flex";
    chatForm.style.display = "flex";
  }
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function markdownToHtml(text) {
  let html = escapeHtml(text);

  // Code blocks (triple backticks)
  html = html.replace(/```([\s\S]*?)```/g, "<pre><code>$1</code></pre>");

  // Inline code (single backticks)
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");

  // Bold (**text**)
  html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/__([^_]+)__/g, "<strong>$1</strong>");

  // Italic (*text* or _text_)
  html = html.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  html = html.replace(/_([^_]+)_/g, "<em>$1</em>");

  // Links [text](url)
  html = html.replace(/\[(.*?)\]\((https?:[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');

  // Headings
  html = html.replace(/^### (.*?)$/gm, "<h3>$1</h3>");
  html = html.replace(/^## (.*?)$/gm, "<h2>$1</h2>");
  html = html.replace(/^# (.*?)$/gm, "<h1>$1</h1>");

  // Lists
  html = html.replace(/^\* (.*?)$/gm, "<li>$1</li>");
  html = html.replace(/(<li>.*<\/li>)/s, "<ul>$1</ul>");

  // Line breaks
  html = html.replace(/\n/g, "<br/>");

  return html;
}

function setLoading(el, loading) {
  if (!el) return;
  el.disabled = !!loading;
  if (loading) {
    el.dataset.prevText = el.textContent;
    el.textContent = "...";
  } else if (el.dataset.prevText) {
    el.textContent = el.dataset.prevText;
    delete el.dataset.prevText;
  }
}

async function api(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail || JSON.stringify(data);
    } catch (e) {
      /* ignore */
    }
    throw new Error(detail);
  }
  const text = await res.text();
  return text ? JSON.parse(text) : null;
}

function renderMessage(role, content, ts = new Date(), tools = null) {
  const node = messageTemplate.content.cloneNode(true);
  const msgEl = node.firstElementChild;
  msgEl.classList.add(role === "human" ? "human" : "ai");
  node.querySelector(".message-meta").textContent = `${role} • ${new Date(ts).toLocaleTimeString()}`;
  node.querySelector(".message-body").innerHTML = markdownToHtml(content);

  // Add tool usage if present
  if (tools && tools.length > 0) {
    const toolsEl = document.createElement("div");
    toolsEl.className = "tools-used";
    toolsEl.innerHTML = `🔧 Tools used: ${tools.join(", ")}`;
    msgEl.appendChild(toolsEl);
  }

  messagesEl.appendChild(node);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function showTypingIndicator() {
  const node = messageTemplate.content.cloneNode(true);
  const msgEl = node.firstElementChild;
  msgEl.classList.add("ai", "typing-indicator");
  msgEl.id = "typing-indicator";
  node.querySelector(".message-meta").textContent = "ai • thinking";
  const bodyEl = node.querySelector(".message-body");
  bodyEl.innerHTML = `<div class="typing-dots"><span></span><span></span><span></span></div>`;
  messagesEl.appendChild(node);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return msgEl;
}

function removeTypingIndicator() {
  const indicator = document.getElementById("typing-indicator");
  if (indicator) {
    indicator.remove();
  }
}

function ensureStreamBubble() {
  // If a streaming bubble already exists, reuse it
  if (currentStreamEl && messagesEl.contains(currentStreamEl)) return currentStreamEl;

  // Try to grab any existing streaming bubble from DOM (fallback safety)
  const existing = messagesEl.querySelector(".ai-stream");
  if (existing) {
    currentStreamEl = existing;
    currentStreamMeta = currentStreamEl.querySelector(".message-meta");
    return currentStreamEl;
  }

  // Remove typing indicator and create streaming bubble
  removeTypingIndicator();

  // Otherwise create a new one
  const node = messageTemplate.content.cloneNode(true);
  currentStreamEl = node.firstElementChild;
  currentStreamEl.classList.add("ai", "ai-stream");
  currentStreamMeta = currentStreamEl.querySelector(".message-meta");
  currentStreamMeta.textContent = "ai • streaming";
  messagesEl.appendChild(currentStreamEl);
  return currentStreamEl;
}

function renderSessions(list) {
  sessionsEl.innerHTML = "";
  list.forEach((s) => {
    const div = document.createElement("div");
    div.className = "session-item" + (s.id === currentSessionId ? " active" : "");

    const contentDiv = document.createElement("div");
    contentDiv.className = "session-item-content";
    const displayName = s.session_name || s.id;
    const idShort = s.id.slice(0, 8);
    contentDiv.innerHTML = `<div>${displayName}</div><div class="muted">ID: ${idShort} • RAG: ${s.rag_enabled ? "on" : "off"}</div>`;
    contentDiv.style.cursor = "pointer";
    contentDiv.style.flex = "1";
    contentDiv.onclick = () => loadSession(s.id);

    const button = document.createElement("button");
    button.className = "btn session-btn";
    button.textContent = "⚙";
    button.onclick = async (e) => {
      e.stopPropagation();
      currentSessionId = s.id;
      const modal = document.getElementById("session-modal");
      const metaEl = document.getElementById("modal-session-meta");
      // Open the modal immediately for feedback
      modal.style.display = "flex";
      if (metaEl) metaEl.textContent = "Loading session...";
      // Make sure action buttons start disabled until load completes
      deleteSessionBtn.disabled = true;
      enableRagBtn.disabled = true;
      try {
        await loadSession(s.id);
      } catch (err) {
        if (metaEl) metaEl.textContent = `Failed to load session: ${err?.message || err}`;
      }
    };

    div.appendChild(contentDiv);
    div.appendChild(button);
    sessionsEl.appendChild(div);
  });
}

async function loadSessions() {
  const data = await api("/sessions");
  renderSessions(data);
}

async function createSession() {
  setLoading(createSubmitBtn, true);
  try {
    const session_name = createSessionNameInput.value.trim();
    const rag_path = createRagPathInput.value.trim();
    const rag_description = createRagDescriptionInput.value.trim();
    // Close modal immediately; proceed with API calls
    createModal.style.display = "none";

    const res = await api("/sessions/create", {
      method: "POST",
      body: JSON.stringify(session_name ? { session_name } : {}),
    });
    currentSessionId = res.session_id;

    if (rag_path) {
      try {
        const ragPayload = { documents_path: rag_path };
        if (rag_description) {
          ragPayload.description = rag_description;
        }
        const ragRes = await api(`/sessions/${currentSessionId}/enable-rag`, {
          method: "POST",
          body: JSON.stringify(ragPayload),
        });
        alert(ragRes.message || "RAG enabled");
      } catch (err) {
        alert(`RAG enable failed: ${err.message}`);
      }
    }
    createSessionNameInput.value = "";
    createRagPathInput.value = "";
    createRagDescriptionInput.value = "";
    await loadSessions();
    await loadSession(currentSessionId);
  } catch (e) {
    alert(`Create session failed: ${e.message}`);
  } finally {
    setLoading(createSubmitBtn, false);
  }
}

async function deleteSession() {
  if (!currentSessionId) return;
  setLoading(deleteSessionBtn, true);
  try {
    await api(`/sessions/${currentSessionId}`, { method: "DELETE" });
    currentSessionId = null;
    messagesEl.innerHTML = "";
    ragStatusEl.textContent = "";
    ragPathInput.value = "";
    document.getElementById("modal-session-meta").textContent = "Select a session to view details.";
    deleteSessionBtn.disabled = true;
    enableRagBtn.disabled = true;
    document.getElementById("session-modal").style.display = "none";
    await loadSessions();
  } catch (e) {
    alert(`Delete failed: ${e.message}`);
  } finally {
    setLoading(deleteSessionBtn, false);
  }
}

async function loadSession(id) {
  try {
    const session = await api(`/sessions/${id}`);
    currentSessionId = id;
    deleteSessionBtn.disabled = false;
    enableRagBtn.disabled = false;

    // Show chat interface and hide welcome state
    toggleWelcomeState(false);

    // Update modal
    document.getElementById("modal-session-meta").textContent = `${session.session_name || `Session ${id}`} • ID: ${id} • RAG: ${session.rag_enabled ? "on" : "off"}`;
    document.getElementById("rag-status").textContent = session.rag_documents_path ? `Docs: ${session.rag_documents_path}` : "No RAG path";
    ragPathInput.value = session.rag_documents_path || "";
    ragDescriptionInput.value = session.rag_description || "";

    messagesEl.innerHTML = "";
    (session.messages || []).forEach((m) => renderMessage(m.role, m.content, m.created_at));

    await loadSessions();
  } catch (e) {
    alert(`Load session failed: ${e.message}`);
  }
}

async function enableRag() {
  if (!currentSessionId) return;
  const path = ragPathInput.value.trim();
  if (!path) {
    alert("Enter a documents path");
    return;
  }
  const description = ragDescriptionInput.value.trim();
  setLoading(enableRagBtn, true);
  try {
    const ragPayload = { documents_path: path };
    if (description) {
      ragPayload.description = description;
    }
    const res = await api(`/sessions/${currentSessionId}/enable-rag`, {
      method: "POST",
      body: JSON.stringify(ragPayload),
    });
    ragStatusEl.textContent = res.message;
    await loadSession(currentSessionId);
  } catch (e) {
    alert(`Enable RAG failed: ${e.message}`);
  } finally {
    setLoading(enableRagBtn, false);
  }
}

async function sendMessage(event) {
  event.preventDefault();
  if (streaming || !currentSessionId) return;
  const text = chatInput.value.trim();
  if (!text) return;

  renderMessage("human", text);
  chatInput.value = "";

  // Show typing indicator
  showTypingIndicator();

  try {
    streaming = true;
    currentStreamEl = null;
    currentStreamMeta = null;
    const res = await fetch(`${API_BASE}/query/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: text, session_id: currentSessionId }),
    });

    if (!res.body) throw new Error("No response body");

    let buffer = "";
    const reader = res.body.getReader();
    let aiBuffer = "";
    let toolsUsed = [];

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += new TextDecoder().decode(value, { stream: true });

      const parts = buffer.split("\n\n");
      buffer = parts.pop() || "";

      for (const part of parts) {
        const line = part.trim();
        if (!line.startsWith("data:")) continue;
        const payload = line.slice(5).trim();
        if (!payload) continue;
        let data;
        try {
          data = JSON.parse(payload);
        } catch (e) {
          console.warn("Bad SSE payload", payload);
          continue;
        }

        if (data.type === "content" && data.content) {
          aiBuffer += data.content;
          const bubble = ensureStreamBubble();
          const bodyEl = bubble.querySelector(".message-body");
          bodyEl.innerHTML = markdownToHtml(aiBuffer);
          bodyEl.classList.add("streaming-text");
          messagesEl.scrollTop = messagesEl.scrollHeight;
        }

        // Track tool usage
        if (data.type === "tool_use" || data.type === "tool") {
          const toolName = data.tool_name || data.tool || "unknown tool";
          if (!toolsUsed.includes(toolName)) {
            toolsUsed.push(toolName);
          }
        }

        if (data.type === "final_answer") {
          removeTypingIndicator();
          const content = data.answer;

          // Extract tools from final_answer if provided
          if (data.tools_used && Array.isArray(data.tools_used)) {
            toolsUsed = [...data.tools_used]; // Make a copy
          }


          if (currentStreamEl) {
            currentStreamEl.classList.remove("ai-stream");
            currentStreamMeta.textContent = `ai • ${new Date().toLocaleTimeString()}`;
            const bodyEl = currentStreamEl.querySelector(".message-body");
            bodyEl.innerHTML = markdownToHtml(content || aiBuffer);
            bodyEl.classList.remove("streaming-text");

            // Add tools used - check before resetting
            console.log("About to add tools, count:", toolsUsed.length, "tools:", toolsUsed);
            if (toolsUsed && toolsUsed.length > 0) {
              const toolsEl = document.createElement("div");
              toolsEl.className = "tools-used";
              toolsEl.innerHTML = `🔧 Tools used: ${toolsUsed.join(", ")}`;
              currentStreamEl.appendChild(toolsEl);
              console.log("Tools element added to message");
            }

            currentStreamEl = null;
            currentStreamMeta = null;
          } else {
            renderMessage("ai", content, new Date(), toolsUsed.length > 0 ? toolsUsed : null);
          }
          aiBuffer = "";
          toolsUsed = [];
        }

        if (data.type === "error") {
          removeTypingIndicator();
          alert(data.error || "Streaming error");
        }
      }
    }
  } catch (e) {
    removeTypingIndicator();
    alert(`Send failed: ${e.message}`);
  } finally {
    streaming = false;
    currentStreamEl = null;
    currentStreamMeta = null;
  }
}

deleteSessionBtn.onclick = deleteSession;
enableRagBtn.onclick = enableRag;
chatForm.addEventListener("submit", sendMessage);

createCloseBtn.onclick = () => (createModal.style.display = "none");
createCancelBtn.onclick = () => (createModal.style.display = "none");
createForm.addEventListener("submit", (e) => {
  e.preventDefault();
  createSession();
});
createSessionBtn.onclick = () => {
  createModal.style.display = "flex";
};

loadSessions().catch((e) => console.error(e));
