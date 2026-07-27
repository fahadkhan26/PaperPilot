import { useEffect, useRef } from 'react';
import ChatBubble from '../ChatBubble/ChatBubble.jsx';
import './ChatMessages.css';

export default function ChatMessages({ messages }) {
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages]);

  return (
    <div className="chat-messages">
      {messages.length === 0 && (
        <p className="chat-messages__empty">Attach a PDF, then ask anything about it.</p>
      )}
      {messages.map((m) => (
        <ChatBubble key={m.id} role={m.role} text={m.text} status={m.status} />
      ))}
      <div ref={endRef} />
    </div>
  );
}
