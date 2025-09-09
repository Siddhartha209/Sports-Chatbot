import React, { useState } from 'react';
import './chatInput.css';

const ChatInput = ({ onSend }) => {
  const [message, setMessage] = useState('');

  const handleSend = () => {
    const trimmed = message.trim();
    if (trimmed !== '') {
      onSend(trimmed);   // ✅ send message to App
      setMessage('');
    }
  };

  return (
    <div className="chat-input-container">
      <textarea
        className="chat-textarea"
        placeholder="Type your message..."
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
          }
        }}
        rows={1}
      />
      <button className="send-btn" onClick={handleSend}>➤</button>
    </div>
  );
};

export default ChatInput;
