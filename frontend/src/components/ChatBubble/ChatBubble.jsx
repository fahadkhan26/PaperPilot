import TypingDots from '../TypingDots/TypingDots.jsx';
import './ChatBubble.css';

export default function ChatBubble({ role, text, status }) {
  const isUser = role === 'user';
  const isError = status === 'error';
  const isPending = status === 'pending';
  const isStreaming = status === 'streaming';

  const bubbleClass = [
    'chat-bubble',
    isUser ? 'chat-bubble--user' : 'chat-bubble--ai',
    isError ? 'chat-bubble--error' : '',
  ]
    .join(' ')
    .trim();

  return (
    <div className={`chat-row ${isUser ? 'chat-row--user' : 'chat-row--ai'}`}>
      <div className={bubbleClass}>
        {isPending ? (
          <TypingDots />
        ) : (
          <span>
            {text}
            {isStreaming && <span className="chat-cursor">▍</span>}
          </span>
        )}
      </div>
    </div>
  );
}
