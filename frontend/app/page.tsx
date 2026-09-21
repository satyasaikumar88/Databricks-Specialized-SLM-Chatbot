'use client';

import { useEffect, useState } from 'react';

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

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Hi! I can help with Databricks architecture, Delta Lake, Spark tuning, Unity Catalog, and PySpark examples. Ask me anything.',
    },
  ]);
  const [sources, setSources] = useState<SourceDoc[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

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

  async function sendPrompt() {
    const trimmed = message.trim();
    if (!trimmed || loading) {
      return;
    }

    setLoading(true);
    setError('');
    const userMessage: Message = { role: 'user', content: trimmed };
    setMessages((prev) => [...prev, userMessage]);
    setMessage('');

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: trimmed, history: messages }),
      });

      if (!response.ok) {
        throw new Error('The backend could not answer the question.');
      }

      const data = await response.json();
      const assistantMessage: Message = { role: 'assistant', content: data.answer };
      setMessages((prev) => [...prev, assistantMessage]);
      setSources(data.sources || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.');
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Sorry, I hit an error while generating that answer.' }]);
    } finally {
      setLoading(false);
    }
  }

  function clearConversation() {
    setMessages([
      {
        role: 'assistant',
        content: 'Conversation cleared. Ask a Databricks question and I will respond with grounded guidance.',
      },
    ]);
    setSources([]);
    setError('');
  }

  return (
    <main className="chat-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-badge">D</div>
          <h1>Databricks-Specialized SLM Chatbot</h1>
        </div>
        <button className="clear-btn" onClick={clearConversation}>Clear conversation</button>
      </header>

      <div className="chat-layout">
        <section className="panel chat-panel">
          <div className="message-list">
            {messages.map((msg, index) => (
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
