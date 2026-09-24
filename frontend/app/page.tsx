'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface SourceDoc {
  id: string;
  title: string;
  source: string;
  snippet: string;
  score: number;
}

interface User {
  id: number;
  full_name: string;
  email: string;
  created_at: string;
  updated_at: string;
}

interface ConversationThread {
  id: string;
  title: string;
  messages: Message[];
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
function createConversationThread(): ConversationThread {
  return {
    id: `conversation-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`,
    title: 'New Chat',
    messages: [],
  };
}

function conversationTitleFromMessage(content: string) {
  const normalized = content.trim().replace(/\s+/g, ' ').replace(/[.!?]+$/, '');
  const lower = normalized.toLowerCase();
  let title = normalized;

  if (lower.startsWith('what is ')) {
    title = normalized.slice(8);
  } else if (lower.startsWith('how does ') && lower.endsWith(' work')) {
    title = normalized.slice(9, -5).trim();
  } else if (lower.startsWith('explain ') && lower.endsWith(' architecture')) {
    title = `${normalized.slice(8, -12).trim()} Architecture`;
  } else {
    const csvMatch = normalized.match(/^how can i read (.+?) using (.+)$/i);
    if (csvMatch) {
      title = `Reading ${csvMatch[1]} with ${csvMatch[2]}`;
    }
  }

  title = title.replace(/\bbronze\s+silver\s+gold\b/i, 'Bronze-Silver-Gold').replace(/[,:;]+$/, '').trim();
  if (title.length > 35) {
    title = title.slice(0, 35).replace(/\s+\S*$/, '').trim();
  }
  return title || 'New Chat';
}

function escapeHtml(value: string) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function renderMarkdownCode(text: string) {
  const codeBlocks = Array.from(text.matchAll(/```([\w-]*)\n([\s\S]*?)```/g));
  if (!codeBlocks.length) {
    return text;
  }

  let parsed = text;
  for (const match of codeBlocks) {
    const [, lang, code] = match;
    const html = `\n<div class="code-header"><button class="copy-btn" data-code="${escapeHtml(code)}">Copy</button></div><pre><code class="language-${lang || 'plaintext'}">${escapeHtml(code.trim())}</code></pre>`;
    parsed = parsed.replace(match[0], html);
  }
  return parsed;
}

export default function Page() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [threads, setThreads] = useState<ConversationThread[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [threadSources, setThreadSources] = useState<Record<string, SourceDoc[]>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const sidebarRef = useRef<HTMLDivElement | null>(null);
  const sidebarToggleRef = useRef<HTMLButtonElement | null>(null);

  const activeThread = threads.find((thread) => thread.id === activeThreadId) ?? threads[0] ?? null;
  const messages = activeThread?.messages ?? [];
  const sources = activeThreadId ? threadSources[activeThreadId] ?? [] : [];

  useEffect(() => {
    let isMounted = true;

    async function loadCurrentUser() {
      try {
        const response = await fetch(`${API_URL}/auth/me`, {
          method: 'GET',
          credentials: 'include',
          cache: 'no-store',
        });

        if (!response.ok) {
          throw new Error('Session expired');
        }

        const data = await response.json();
        if (isMounted) {
          setUser(data);
        }
      } catch {
        if (isMounted) {
          router.replace('/login');
        }
      } finally {
        if (isMounted) {
          setAuthLoading(false);
        }
      }
    }

    loadCurrentUser();
    return () => {
      isMounted = false;
    };
  }, [router]);

  useEffect(() => {
    if (!user) {
      return;
    }

    async function loadConversations() {
      try {
        const listResponse = await fetch(`${API_URL}/conversations`, {
          method: 'GET',
          credentials: 'include',
          cache: 'no-store',
        });

        if (!listResponse.ok) {
          throw new Error('Unable to fetch conversations');
        }

        const listData = await listResponse.json();
        const loadedThreads: ConversationThread[] = [];

        for (const conversation of listData) {
          const messageResponse = await fetch(`${API_URL}/conversations/${conversation.id}/messages`, {
            method: 'GET',
            credentials: 'include',
            cache: 'no-store',
          });

          const messageData = messageResponse.ok ? await messageResponse.json() : { messages: [] };
          const loadedMessages = (messageData.messages ?? []).map((msg: { role: string; content: string }) => ({
            role: msg.role === 'user' ? 'user' : 'assistant',
            content: msg.content,
          }));
          const firstUserMessage = loadedMessages.find((msg: Message) => msg.role === 'user');
          const generatedTitle = firstUserMessage ? conversationTitleFromMessage(firstUserMessage.content) : 'New Chat';
          loadedThreads.push({
            id: conversation.id,
            title: generatedTitle,
            messages: loadedMessages,
          });
          if (conversation.title !== generatedTitle) {
            void fetch(`${API_URL}/conversations/${conversation.id}`, {
              method: 'PATCH',
              headers: { 'Content-Type': 'application/json' },
              credentials: 'include',
              body: JSON.stringify({ title: generatedTitle }),
            });
          }
        }

        if (loadedThreads.length === 0) {
          const createResponse = await fetch(`${API_URL}/conversations`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ title: 'New Chat' }),
          });

          if (!createResponse.ok) {
            throw new Error('Unable to create a conversation');
          }

          const created = await createResponse.json();
          loadedThreads.push({
            id: created.id,
            title: created.title,
            messages: [],
          });
        }

        setThreads(loadedThreads);
        setActiveThreadId(loadedThreads[0].id);
        setThreadSources((prev) => ({ ...prev, [loadedThreads[0].id]: [] }));
      } catch (err) {
        console.error(err);
        const fallback = createConversationThread();
        setThreads([fallback]);
        setActiveThreadId(fallback.id);
        setThreadSources((prev) => ({ ...prev, [fallback.id]: [] }));
      }
    }

    loadConversations();
  }, [user]);

  useEffect(() => {
    const copyButtons = document.querySelectorAll('.copy-btn');
    copyButtons.forEach((button) => {
      button.addEventListener('click', async () => {
        const code = button.getAttribute('data-code');
        if (code) {
          await navigator.clipboard.writeText(code);
        }
      });
    });
    return () => {
      copyButtons.forEach((button) => button.removeEventListener('click', () => {}));
    };
  }, [messages]);

  useEffect(() => {
    if (!sidebarOpen) {
      return;
    }

    const handlePointerDown = (event: MouseEvent) => {
      const target = event.target as Node;
      const clickedOutsideSidebar = sidebarRef.current && !sidebarRef.current.contains(target);
      const clickedToggle = sidebarToggleRef.current && sidebarToggleRef.current.contains(target);

      if (clickedOutsideSidebar && !clickedToggle) {
        setSidebarOpen(false);
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setSidebarOpen(false);
      }
    };

    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('keydown', handleEscape);

    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [sidebarOpen]);

  async function handleLogout() {
    try {
      await fetch(`${API_URL}/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      });
    } finally {
      router.push('/login');
    }
  }

  async function sendPrompt() {
    const trimmed = message.trim();
    if (!trimmed || loading || !activeThreadId) {
      return;
    }

    setLoading(true);
    setError('');
    const userMessage: Message = { role: 'user', content: trimmed };
    const threadBeforeSend = activeThread ?? { id: activeThreadId, title: 'New Chat', messages: [] };
    const pendingHistory = [...threadBeforeSend.messages, userMessage];

    if (!threadBeforeSend.messages.some((item) => item.role === 'user')) {
      const generatedTitle = conversationTitleFromMessage(trimmed);
      setThreads((prev) => prev.map((thread) => thread.id === activeThreadId ? { ...thread, title: generatedTitle } : thread));
      void fetch(`${API_URL}/conversations/${activeThreadId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ title: generatedTitle }),
      });
    }

    setThreads((prev) =>
      prev.map((thread) =>
        thread.id === activeThreadId ? { ...thread, messages: pendingHistory } : thread,
      ),
    );
    setMessage('');

    try {
      const currentHistory = pendingHistory.map((msg) => ({
        role: msg.role,
        content: msg.content,
      }));

      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          question: trimmed,
          session_id: activeThreadId,
          history: currentHistory,
        }),
      });

      if (response.status === 401) {
        router.replace('/login');
        return;
      }

      if (!response.ok) {
        throw new Error('The backend could not answer the question.');
      }

      const data = await response.json();
      const assistantMessage: Message = { role: 'assistant', content: data.answer };

      setThreads((prev) =>
        prev.map((thread) =>
          thread.id === activeThreadId ? { ...thread, messages: [...thread.messages, assistantMessage] } : thread,
        ),
      );
      setThreadSources((prev) => ({ ...prev, [activeThreadId]: data.sources || [] }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.');
      setThreads((prev) =>
        prev.map((thread) =>
          thread.id === activeThreadId
            ? { ...thread, messages: [...thread.messages, { role: 'assistant', content: 'Sorry, I hit an error while generating that answer.' }] }
            : thread,
        ),
      );
    } finally {
      setLoading(false);
    }
  }

  async function createNewConversation() {
    try {
      const response = await fetch(`${API_URL}/conversations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ title: 'New Chat' }),
      });

      if (!response.ok) {
        throw new Error('Unable to create a new conversation');
      }

      const created = await response.json();
      const nextThread: ConversationThread = {
        id: created.id,
        title: 'New Chat',
        messages: [],
      };

      setThreads((prev) => [...prev, nextThread]);
      setActiveThreadId(nextThread.id);
      setThreadSources((prev) => ({ ...prev, [nextThread.id]: [] }));
      setError('');
    } catch (err) {
      const fallback = createConversationThread();
      setThreads((prev) => [...prev, fallback]);
      setActiveThreadId(fallback.id);
      setThreadSources((prev) => ({ ...prev, [fallback.id]: [] }));
      setError(err instanceof Error ? err.message : 'Unable to create a new conversation');
    }
  }

  async function deleteConversation(threadId: string) {
    if (!threadId) {
      return;
    }
    try {
      const response = await fetch(`${API_URL}/conversations/${threadId}`, {
        method: 'DELETE',
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Unable to delete this conversation');
      }

      const remaining = threads.filter((thread) => thread.id !== threadId);
      setThreads(remaining);
      if (remaining.length === 0) {
        const created = await createNewConversation();
        void created;
        return;
      }

      if (activeThreadId === threadId) {
        setActiveThreadId(remaining[0].id);
      }
      setThreadSources((prev) => {
        const next = { ...prev };
        delete next[threadId];
        return next;
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete conversation.');
    }
  }

  function clearConversation() {
    if (!activeThreadId) {
      return;
    }

    setThreads((prev) =>
      prev.map((thread) =>
        thread.id === activeThreadId
          ? {
              ...thread,
              messages: [
                {
                  role: 'assistant',
                  content: 'Conversation cleared. Ask a Databricks question and I will respond with grounded guidance.',
                },
              ],
            }
          : thread,
      ),
    );
    setThreadSources((prev) => ({ ...prev, [activeThreadId]: [] }));
    setError('');
  }

  if (authLoading) {
    return (
      <main className="chat-shell">
        <div className="auth-loading">Checking your session…</div>
      </main>
    );
  }

  return (
    <main className="chat-shell">
      <header className="topbar">
        <div className="topbar-left">
          <button
            ref={sidebarToggleRef}
            type="button"
            className="menu-btn"
            aria-label="Toggle conversations menu"
            onClick={() => setSidebarOpen((open) => !open)}
          >
            ☰
          </button>
          <div className="brand">
            <div className="brand-badge">D</div>
            <div>
              <h1>Databricks-Specialized SLM Chatbot</h1>
              {user && <div className="user-chip">Hello, {user.full_name}</div>}
            </div>
          </div>
        </div>
        <div className="topbar-actions">
          <button className="clear-btn" onClick={createNewConversation}>New conversation</button>
          <button className="clear-btn" onClick={clearConversation}>Clear conversation</button>
          <button className="logout-btn" onClick={handleLogout}>Logout</button>
        </div>
      </header>

      {sidebarOpen && <button type="button" className="sidebar-backdrop" aria-label="Close conversation sidebar" onClick={() => setSidebarOpen(false)} />}

      <aside
        ref={sidebarRef}
        className={`panel conversation-sidebar ${sidebarOpen ? 'open' : ''}`}
        aria-label="Conversation sidebar"
      >
        <div className="sidebar-header">
          <h2>Conversations</h2>
          <button type="button" className="icon-btn" aria-label="Close conversations" onClick={() => setSidebarOpen(false)}>
            ✕
          </button>
        </div>

        <button type="button" className="primary-btn sidebar-new-btn" onClick={() => { void createNewConversation(); setSidebarOpen(false); }}>
          + New Conversation
        </button>

        <div className="conversation-list">
          {threads.length === 0 ? (
            <div className="empty-state">No conversations yet.</div>
          ) : (
            threads.map((thread) => (
              <div
                key={thread.id}
                className={`conversation-item ${thread.id === activeThreadId ? 'active' : ''}`}
              >
                <button
                  type="button"
                  className="conversation-select"
                  onClick={() => {
                    setActiveThreadId(thread.id);
                    setSidebarOpen(false);
                  }}
                >
                  {thread.title}
                </button>
                <button
                  type="button"
                  className="conversation-delete"
                  onClick={() => deleteConversation(thread.id)}
                >
                  Delete
                </button>
              </div>
            ))
          )}
        </div>
      </aside>

      <div className="chat-layout">
        <section className="panel chat-panel">
          <div className="message-list">
            {messages.length === 0 ? (
              <div className="empty-state">
                <h2>New Chat</h2>
                <p>Ask me anything about Databricks.</p>
              </div>
            ) : messages.map((msg, index) => (
                <div key={`${msg.role}-${index}`} className={`message-row ${msg.role}`}>
                  <div className={`message ${msg.role}`} dangerouslySetInnerHTML={{ __html: renderMarkdownCode(msg.content) }} />
                </div>
              ))}
            {loading && <div className="message-row assistant"><div className="message assistant">Generating answer...</div></div>}
          </div>

          <div className="input-panel">
            <form
              className="prompt-form"
              onSubmit={(e) => {
                e.preventDefault();
                sendPrompt();
              }}
            >
              <textarea
                className="prompt-input"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Ask about Delta Lake, Spark performance, Unity Catalog, or write sample PySpark..."
              />
              <div className="actions">
                <span className="status">{error || (loading ? 'Thinking…' : 'Ready')}</span>
                <button className="send-btn" type="submit" disabled={loading || !message.trim()}>
                  {loading ? 'Sending…' : 'Send'}
                </button>
              </div>
            </form>
          </div>
        </section>

        <aside className="panel sources-panel">
          <h2>Sources</h2>
          {sources.length === 0 ? (
            <div className="empty-state">No sources yet. Ask a question to retrieve Databricks documentation.</div>
          ) : (
            <div className="source-list">
              {sources.map((doc) => (
                <div key={doc.id} className="source-card">
                  <h3>{doc.title}</h3>
                  <a href={doc.source} target="_blank" rel="noreferrer">
                    {doc.source}
                  </a>
                  <p>{doc.snippet}</p>
                </div>
              ))}
            </div>
          )}
        </aside>
      </div>
    </main>
  );
}
