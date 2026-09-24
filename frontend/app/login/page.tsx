'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FormEvent, useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email, password, remember_me: rememberMe }),
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => ({ detail: 'Login failed.' }));
        throw new Error(payload.detail || 'Login failed.');
      }

      router.push('/');
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to sign in.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <main className="login-page-shell">
        <div className="login-page-glow login-glow-one" aria-hidden="true" />
        <div className="login-page-glow login-glow-two" aria-hidden="true" />

        <section className="login-layout">
          <div className="login-brand-panel">
            <div className="brand-header">
              <div className="brand-mark" aria-label="Databricks Learning Assistant icon">
                <div className="brand-mark-core">
                  <span className="brand-node brand-node-1" />
                  <span className="brand-node brand-node-2" />
                  <span className="brand-node brand-node-3" />
                </div>
              </div>
              <div>
                <p className="eyebrow">AI learning platform</p>
                <h1>Databricks Learning Assistant</h1>
              </div>
            </div>

            <div className="brand-copy">
              <p className="lead">AI-powered learning for Databricks</p>
              <p className="description">Learn Databricks with a focused AI assistant that brings together Qwen, retrieval, and source-backed guidance for real-world data work.</p>
            </div>

            <ul className="feature-list" aria-label="Databricks Learning Assistant benefits">
              <li>Databricks-focused answers</li>
              <li>Source-backed responses</li>
              <li>Interactive learning</li>
              <li>Spark, Delta Lake &amp; Unity Catalog support</li>
            </ul>
          </div>

          <div className="login-card-panel">
            <div className="card-header">
              <p className="card-kicker">Welcome back</p>
              <h2>Sign in to continue learning</h2>
            </div>

            <form className="auth-form" onSubmit={handleSubmit}>
              <div className="field">
                <label htmlFor="email">Email</label>
                <div className="input-wrap">
                  <span className="input-icon" aria-hidden="true">@</span>
                  <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="name@databricks.com" required />
                </div>
              </div>

              <div className="field">
                <label htmlFor="password">Password</label>
                <div className="input-wrap">
                  <span className="input-icon" aria-hidden="true">●</span>
                  <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Enter your password" required />
                </div>
              </div>

              <button className="primary-btn" type="submit" disabled={loading}>
                {loading ? 'Signing in…' : 'Sign In'}
              </button>

              <div className="form-error" role="alert" aria-live="polite">{error}</div>
            </form>

            <div className="switch-link">
              Don&apos;t have an account? <Link href="/signup">Create one</Link>
            </div>
          </div>
        </section>
      </main>

      <style jsx>{`
        .login-page-shell {
          position: relative;
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 32px 24px;
          overflow: hidden;
          background:
            radial-gradient(circle at top left, rgba(79, 70, 229, 0.18), transparent 28%),
            radial-gradient(circle at bottom right, rgba(34, 211, 238, 0.12), transparent 30%),
            linear-gradient(135deg, #06111d 0%, #0a1729 40%, #091420 100%);
        }

        .login-page-shell::before {
          content: '';
          position: absolute;
          inset: 0;
          background-image:
            linear-gradient(rgba(148, 163, 184, 0.06) 1px, transparent 1px),
            linear-gradient(90deg, rgba(148, 163, 184, 0.05) 1px, transparent 1px);
          background-size: 34px 34px;
          mask-image: radial-gradient(circle at center, black 35%, transparent 100%);
          pointer-events: none;
        }

        .login-page-glow {
          position: absolute;
          border-radius: 9999px;
          filter: blur(72px);
          pointer-events: none;
          opacity: 0.45;
        }

        .login-glow-one {
          width: 360px;
          height: 360px;
          left: 8%;
          top: 12%;
          background: rgba(79, 70, 229, 0.26);
        }

        .login-glow-two {
          width: 420px;
          height: 420px;
          right: 12%;
          bottom: 10%;
          background: rgba(34, 211, 238, 0.18);
        }

        .login-layout {
          position: relative;
          z-index: 1;
          width: min(1100px, 100%);
          min-height: 660px;
          display: grid;
          grid-template-columns: 1.12fr 0.88fr;
          border: 1px solid rgba(148, 163, 184, 0.18);
          border-radius: 30px;
          background: rgba(11, 17, 29, 0.78);
          box-shadow: 0 22px 60px rgba(2, 6, 23, 0.48);
          backdrop-filter: blur(10px);
          overflow: hidden;
        }

        .login-brand-panel {
          position: relative;
          padding: 52px 52px 40px;
          background: linear-gradient(180deg, rgba(11, 21, 36, 0.8), rgba(15, 22, 34, 0.92));
          border-right: 1px solid rgba(148, 163, 184, 0.12);
        }

        .brand-header {
          display: flex;
          align-items: center;
          gap: 18px;
          margin-bottom: 30px;
        }

        .brand-mark {
          width: 62px;
          height: 62px;
          border-radius: 18px;
          display: grid;
          place-items: center;
          background: linear-gradient(135deg, rgba(79, 70, 229, 0.96), rgba(6, 182, 212, 0.9));
          box-shadow: 0 18px 34px rgba(37, 99, 235, 0.28);
          border: 1px solid rgba(255, 255, 255, 0.12);
        }

        .brand-mark-core {
          position: relative;
          width: 36px;
          height: 36px;
          border-radius: 12px;
          background: rgba(5, 12, 19, 0.3);
          border: 1px solid rgba(255, 255, 255, 0.14);
        }

        .brand-node {
          position: absolute;
          display: block;
          border-radius: 9999px;
          background: rgba(255, 255, 255, 0.9);
          box-shadow: 0 0 0 4px rgba(148, 163, 184, 0.04);
        }

        .brand-node-1 {
          width: 8px;
          height: 8px;
          left: 7px;
          top: 14px;
        }

        .brand-node-2 {
          width: 9px;
          height: 9px;
          left: 16px;
          top: 7px;
        }

        .brand-node-3 {
          width: 8px;
          height: 8px;
          right: 7px;
          bottom: 8px;
        }

        .eyebrow {
          margin: 0 0 8px;
          font-size: 0.72rem;
          letter-spacing: 0.13em;
          text-transform: uppercase;
          color: #8ec7ff;
        }

        .brand-header h1 {
          margin: 0;
          font-size: clamp(2.1rem, 3vw, 3.2rem);
          line-height: 1.04;
          letter-spacing: -0.06em;
          color: #edf6ff;
        }

        .brand-copy {
          margin-top: 52px;
          max-width: 470px;
        }

        .lead {
          margin: 0;
          font-size: clamp(1.15rem, 1.6vw, 1.6rem);
          color: #dfeeff;
          letter-spacing: -0.04em;
          line-height: 1.5;
        }

        .description {
          margin-top: 16px;
          color: rgba(191, 214, 240, 0.8);
          font-size: 1.02rem;
          line-height: 1.8;
          max-width: 460px;
        }

        .feature-list {
          list-style: none;
          padding: 0;
          margin: 32px 0 0;
          display: grid;
          gap: 14px;
          max-width: 380px;
        }

        .feature-list li {
          position: relative;
          padding-left: 30px;
          color: #e3f0ff;
          font-size: 1rem;
          line-height: 1.6;
        }

        .feature-list li::before {
          content: '✓';
          position: absolute;
          left: 0;
          top: 0;
          color: #72f5c5;
          font-weight: 700;
        }

        .login-card-panel {
          display: flex;
          flex-direction: column;
          justify-content: center;
          padding: 42px 44px;
          background: rgba(7, 12, 20, 0.7);
        }

        .card-header {
          margin-bottom: 26px;
        }

        .card-kicker {
          margin: 0 0 12px;
          font-size: 0.72rem;
          letter-spacing: 0.14em;
          text-transform: uppercase;
          color: #8ec7ff;
        }

        .card-header h2 {
          margin: 0;
          font-size: clamp(2rem, 2.8vw, 2.5rem);
          line-height: 1.08;
          letter-spacing: -0.05em;
          color: #f4f8ff;
        }

        .auth-form {
          display: flex;
          flex-direction: column;
          gap: 18px;
        }

        .field {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .field label {
          color: #dfe9f8;
          font-size: 0.94rem;
          font-weight: 600;
        }

        .input-wrap {
          display: flex;
          align-items: center;
          gap: 10px;
          border: 1px solid rgba(148, 163, 184, 0.22);
          border-radius: 14px;
          background: rgba(12, 18, 28, 0.8);
          transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }

        .input-wrap:focus-within {
          border-color: rgba(99, 102, 241, 0.95);
          box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.16);
        }

        .input-icon {
          width: 36px;
          text-align: center;
          color: #8bb2d9;
          font-size: 0.9rem;
          font-weight: 700;
          opacity: 0.95;
        }

        .field input {
          flex: 1;
          border: none;
          background: transparent;
          color: #edf5ff;
          padding: 15px 14px 15px 0;
          font-size: 1rem;
          outline: none;
        }

        .field input::placeholder {
          color: rgba(171, 198, 228, 0.6);
        }

        .primary-btn {
          width: 100%;
          border: none;
          border-radius: 14px;
          padding: 15px 18px;
          font-size: 1rem;
          font-weight: 700;
          letter-spacing: -0.02em;
          color: #f7fbff;
          background: linear-gradient(135deg, #4f46e5 0%, #36b3ff 50%, #10b9d4 100%);
          box-shadow: 0 16px 28px rgba(79, 70, 229, 0.26);
          cursor: pointer;
          transition: transform 0.18s ease, box-shadow 0.2s ease, opacity 0.2s ease;
        }

        .primary-btn:hover:not(:disabled) {
          transform: translateY(-1px);
          box-shadow: 0 18px 32px rgba(79, 70, 229, 0.32);
        }

        .primary-btn:disabled {
          opacity: 0.75;
          cursor: wait;
        }

        .form-error {
          min-height: 20px;
          color: #fca5a5;
          font-size: 0.9rem;
          line-height: 1.4;
        }

        .switch-link {
          margin-top: 24px;
          text-align: center;
          color: rgba(199, 216, 238, 0.9);
          font-size: 0.96rem;
        }

        .switch-link a {
          color: #8ec7ff;
          text-decoration: none;
          font-weight: 600;
        }

        .switch-link a:hover {
          text-decoration: underline;
        }

        @media (max-width: 900px) {
          .login-layout {
            grid-template-columns: 1fr;
            min-height: auto;
          }

          .login-brand-panel {
            border-right: none;
            border-bottom: 1px solid rgba(148, 163, 184, 0.12);
            padding: 36px 28px 30px;
          }

          .login-card-panel {
            padding: 32px 24px 30px;
          }

          .brand-copy {
            margin-top: 28px;
          }
        }

        @media (max-width: 560px) {
          .login-page-shell {
            padding: 20px 14px;
          }

          .login-brand-panel,
          .login-card-panel {
            padding-left: 20px;
            padding-right: 20px;
          }

          .brand-header {
            flex-direction: column;
            align-items: flex-start;
          }

          .brand-header h1 {
            font-size: 2.2rem;
          }

          .card-header h2 {
            font-size: 1.9rem;
          }
        }
      `}</style>
    </>
  );
}
