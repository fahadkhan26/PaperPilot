import { useCallback, useState } from 'react';
import { streamChat } from '../services/api.js';

let idCounter = 0;
const nextId = () => `msg-${Date.now()}-${idCounter++}`;

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);

  const sendMessage = useCallback(
    (query) => {
      const trimmed = query.trim();
      if (!trimmed || isStreaming) return;

      const userMessage = { id: nextId(), role: 'user', text: trimmed, status: 'done' };
      const aiId = nextId();
      const aiMessage = { id: aiId, role: 'ai', text: '', status: 'pending' };

      setMessages((prev) => [...prev, userMessage, aiMessage]);
      setIsStreaming(true);

      const patchAiMessage = (patch) => {
        setMessages((prev) =>
          prev.map((m) => (m.id === aiId ? { ...m, ...patch } : m))
        );
      };

      streamChat(
        trimmed,
        (chunk) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === aiId ? { ...m, text: m.text + chunk, status: 'streaming' } : m
            )
          );
        },
        () => {
          patchAiMessage({ status: 'done' });
          setIsStreaming(false);
        },
        (errorMessage) => {
          patchAiMessage({ text: errorMessage, status: 'error' });
          setIsStreaming(false);
        }
      );
    },
    [isStreaming]
  );

  return { messages, isStreaming, sendMessage };
}
