import './ChatHeader.css';

export default function ChatHeader({ fileName, status, errorMessage }) {
  const label = () => {
    if (status === 'uploading') return 'Uploading document...';
    if (status === 'error') return errorMessage || 'Upload failed';
    if (fileName) return fileName;
    return 'Uploaded PDF Name';
  };

  return (
    <div className={`chat-header ${status === 'error' ? 'chat-header--error' : ''}`}>
      <span className="chat-header__label">{label()}</span>
    </div>
  );
}
