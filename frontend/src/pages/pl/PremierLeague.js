import React, { useState, useRef, useEffect } from "react";
import ChatInput from "../../components/chatInput/chatInput";
import "./PremierLeague.css";

const PremierLeague = () => {
  // Load messages from localStorage if available
  const [messages, setMessages] = useState(() => {
    const saved = localStorage.getItem("plMessages");
    return saved ? JSON.parse(saved) : [];
  });

  const messagesEndRef = useRef(null);

  // Send user message to backend (Flask API)
  const handleSend = async (text) => {
    if (!text.trim()) return;
    const timestamp = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    const userMessage = { text, sender: "user", timestamp };

    // Add user message to chat first
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    localStorage.setItem("plMessages", JSON.stringify(newMessages));

    try {
      const res = await fetch("http://localhost:5000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: text }),
      });

      const data = await res.json();
      const botMessage = { text: data.response, sender: "bot" };

      const updatedMessages = [...newMessages, botMessage];
      setMessages(updatedMessages);
      localStorage.setItem("plMessages", JSON.stringify(updatedMessages));
    } catch (error) {
      const botMessage = { text: "⚠️ Error connecting to server.", sender: "bot" };
      const updatedMessages = [...newMessages, botMessage];
      setMessages(updatedMessages);
      localStorage.setItem("plMessages", JSON.stringify(updatedMessages));
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="pl-page">
      <div className="chat-wrapper">
        <div className="chat-messages">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`chat-message-row ${msg.sender === "user" ? "user" : "bot"}`}
            >
              {msg.sender === "bot" && (
                <img src="/img/bot_pfp.png" alt="Bot" className="profile-pic bot-pic" />
              )}
              <div className={`chat-message ${msg.sender}`}>{msg.text}</div>
              {msg.sender === "user" && (
                <div className="user-info">
                  <img src="/img/user_pfp.png" alt="User" className="profile-pic user-pic" />
                  <div className="timestamp">{msg.timestamp}</div>
                </div>
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
        <ChatInput onSend={handleSend} />
      </div>
    </div>
  );
};

export default PremierLeague;
