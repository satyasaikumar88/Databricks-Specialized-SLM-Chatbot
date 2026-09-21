import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Databricks SLM Chatbot',
  description: 'Databricks-specific local SLM chatbot with RAG and source attribution',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
