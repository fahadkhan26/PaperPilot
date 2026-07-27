import { useCallback, useState } from 'react';
import ChatHeader from '../ChatHeader/ChatHeader.jsx';
import ChatMessages from '../ChatMessages/ChatMessages.jsx';
import ChatInputBar from '../ChatInputBar/ChatInputBar.jsx';
import { uploadPdf } from '../../services/api.js';
import { useChat } from '../../hooks/useChat.js';
import './ChatPanel.css';

export default function ChatPanel() {
  const [fileName, setFileName] = useState('');
  const [uploadStatus, setUploadStatus] = useState('idle'); // idle | uploading | done | error
  const [uploadError, setUploadError] = useState('');
  const { messages, isStreaming, sendMessage } = useChat();

  const handleUpload = useCallback(async (file) => {
    setUploadStatus('uploading');
    setUploadError('');
    try {
      await uploadPdf(file);
      setFileName(file.name);
      setUploadStatus('done');
    } catch (err) {
      setUploadStatus('error');
      setUploadError(err.message || 'Upload failed.');
    }
  }, []);

  return (
    <div className="chat-panel">
      <ChatHeader fileName={fileName} status={uploadStatus} errorMessage={uploadError} />
      <ChatMessages messages={messages} />
      <ChatInputBar
        onUpload={handleUpload}
        onSend={sendMessage}
        disabled={isStreaming || uploadStatus === 'uploading'}
        hasDocument={!!fileName}
      />
    </div>
  );
}
