import { useRef, useState } from 'react';
import './ChatInputBar.css';

export default function ChatInputBar({ onUpload, onSend, disabled, hasDocument }) {
  const fileInputRef = useRef(null);
  const [text, setText] = useState('');

  const handleAttachClick = () => fileInputRef.current?.click();

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) onUpload(file);
    e.target.value = '';
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!text.trim() || disabled) return;
    onSend(text);
    setText('');
  };

  return (
    <form className="chat-input-bar" onSubmit={handleSubmit}>
      <button
        type="button"
        className="chat-input-bar__attach"
        onClick={handleAttachClick}
        aria-label="Attach PDF"
      >
        <PaperclipIcon />
      </button>

      <input
        ref={fileInputRef}
        type="file"
        accept="application/pdf"
        hidden
        onChange={handleFileChange}
      />

      <input
        type="text"
        className="chat-input-bar__field"
        placeholder={
          hasDocument ? 'Ask a question about your document...' : 'Attach a PDF to get started...'
        }
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={disabled || !hasDocument}
      />

      <button
        type="submit"
        className="chat-input-bar__send"
        disabled={disabled || !hasDocument || !text.trim()}
        aria-label="Send message"
      >
        &#10148;
      </button>
    </form>
  );
}

function PaperclipIcon() {
  return (
    <svg
      width="22"
      height="22"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21.44 11.05l-9.19 9.19a5 5 0 0 1-7.07-7.07l9.19-9.19a3.5 3.5 0 0 1 4.95 4.95l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
    </svg>
  );
}
