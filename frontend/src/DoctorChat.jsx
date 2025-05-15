import React, { useEffect, useRef, useState } from 'react';

const DoctorChat = () => {
  // State variables to manage messages, input text, typing status, conversation state, and date picker visibility
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [conversationEnded, setConversationEnded] = useState(false);
  const [showDatePicker, setShowDatePicker] = useState(false);

  // Reference to scroll chat to the latest message automatically
  const chatEndRef = useRef(null);

  // On component mount, reset server state and greet the user
  useEffect(() => {
    fetch('http://localhost:5000/reset', {
      method: 'POST',
    }).catch(error => {
      console.error('Reset error:', error);
    });
    addMessage("Hello! I'm here to help you book a doctor's appointment.\nHow can I assist you today?", 'bot');
  }, []);

  // Scroll chat window to the bottom every time messages change
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, showDatePicker]);

  // Add a new message to the chat log with sender info ('user' or 'bot')
  const addMessage = (text, sender) => {
    setMessages(prev => [...prev, { text, sender }]);
  };

  // Send a message typed by the user to the backend, handle response, and update UI
  const sendMessage = async (message) => {
    addMessage(message, 'user');  // Show user message
    setInput('');                 // Clear input field
    setShowDatePicker(false);     // Hide date picker if visible
    setIsTyping(true);            // Show typing indicator

    try {
      // Call backend chat endpoint with user message
      const response = await fetch('http://localhost:5000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      });

      const data = await response.json();
      addMessage(data.reply, 'bot');

      // If conversation is flagged as ended, update state
      if (data.conversation_end) {
        setConversationEnded(true);
      }
    } catch (err) {
      console.error(err);
      addMessage('Server error. Please try again.', 'bot'); // Show error to user
    } finally {
      setIsTyping(false);// Hide typing indicator
    }
  };
    // Handle user selecting a date from the date picker
  const handleDateSelect = (date) => {
    const formatted = date.toISOString().split('T')[0];
    setShowDatePicker(false);
    sendMessage(`I would like to book an appointment on ${formatted}`);
  };

  const handleSubmit = (e) => {
    e.preventDefault(); // Prevent page reload
    if (input.trim()) {
      sendMessage(input.trim());// Send trimmed input text
    }
  };

  return (
    <div style={styles.body}>
      <div style={styles.chatContainer}>
        <h2 style={styles.header}>Chatbot for scheduling appointments</h2>
        <div style={styles.chatLog}>
          {messages.map((msg, idx) => (
            <div
              key={idx}
              style={{
                ...styles.messageWrapper,
                ...(msg.sender === 'user' ? styles.userWrapper : styles.botWrapper),
              }}
              className="chat-message-wrapper"
            >
              <div style={styles.avatar}>
                {msg.sender === 'user' ? '👤' : '🤖'}
              </div>
              <div
                style={{
                  ...styles.message,
                  ...(msg.sender === 'user' ? styles.user : styles.bot),
                }}
                className="chat-bubble"
              >
                {msg.text.split('\n').map((line, i) => (
                  <div key={i}>{line}</div>
                ))}
              </div>
            </div>
          ))}
          {isTyping && (
            <div style={styles.typingIndicator}>
              Bot is typing<span className="dots">...</span>
            </div>
          )}
          <div ref={chatEndRef} />
          {showDatePicker && (
            <div style={{ ...styles.bot, ...styles.message }}>
              <p>Please choose a date:</p>
              <input
                type="date"
                onChange={(e) => handleDateSelect(new Date(e.target.value))}
                style={{
                  padding: '10px',
                  fontSize: '1em',
                  marginTop: '8px',
                  borderRadius: '6px',
                  border: '1px solid #ccc',
                }}
                min={new Date().toISOString().split('T')[0]}
              />
            </div>
          )}

        </div>

        {!conversationEnded ? (
          <form onSubmit={handleSubmit} style={styles.inputForm}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type a message..."
              style={styles.messageInput}
              required
            />
            <button type="submit" style={styles.sendButton}>Send</button>
            <button
              type="button"
              onClick={() => setShowDatePicker(true)}
              style={styles.dateButton}
            >
              📅
            </button>
          </form>


        ) : (
          <div style={{ textAlign: 'center', marginTop: '20px' }}>
            <button
              style={styles.newChatButton}
              onClick={() => window.location.reload()}
            >
              Start New Conversation
            </button>
          </div>
        )}
      </div>

      {/* Animation Styles */}
      <style>
        {`
        .chat-bubble {
          opacity: 0;
          transform: translateY(10px);
          animation: fadeInUp 0.3s ease forwards;
        }

        @keyframes fadeInUp {
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        ::-webkit-scrollbar {
          width: 6px;
        }

        ::-webkit-scrollbar-thumb {
          background-color: #ccc;
          border-radius: 3px;
        }

        .dots::after {
          content: '';
          display: inline-block;
          width: 1em;
          animation: dots 1s steps(3, end) infinite;
        }

        @keyframes dots {
          0% { content: ''; }
          33% { content: '.'; }
          66% { content: '..'; }
          100% { content: '...'; }
        }

        input:focus {
          border: 1px solid #0078d4 !important;
          box-shadow: 0 0 4px rgba(0, 120, 212, 0.4);
        }

        button:hover {
          transform: translateY(-1px);
        }

        button:active {
          transform: scale(0.98);
        }

        button:hover:not(:disabled) {
          filter: brightness(1.05);
        }
        
        .chat-message-wrapper:hover > div.chat-bubble {
          background-color: #c5e0ff !important; 
          box-shadow: 0 4px 12px rgba(0, 120, 212, 0.2);
          transform: translateY(-2px);
        }

        .chat-message-wrapper:hover > div:first-child {
          box-shadow: 0 0 12px rgba(0, 120, 212, 0.8);
          transform: scale(1.1);
        }

        button:hover {
          filter: brightness(1.1);
          transform: translateY(-2px);
        }
        button:active {
          transform: scale(0.96);
        }

        input[type="date"]:focus {
          border-color: #0078d4 !important;
          box-shadow: 0 0 6px rgba(0, 120, 212, 0.6);
        }

        input[type="text"]:focus {
          border-color: #0078d4 !important;
          box-shadow: 0 0 6px rgba(0, 120, 212, 0.6);
        }

      `}
      </style>

    </div>
  );
};

const styles = {
  body: {
    fontFamily: 'Segoe UI, sans-serif',
    direction: 'ltr',
    backgroundColor: '#f0f2f5',
    minHeight: '100vh',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
  },
  chatContainer: {
    width: '100%',
    maxWidth: '500px',
    background: '#ffffff',
    borderRadius: '16px',
    padding: '20px',
    boxShadow: '0 8px 24px rgba(0,0,0,0.08)',
    display: 'flex',
    flexDirection: 'column',
  },
  header: {
    marginBottom: '16px',
    textAlign: 'center',
    color: '#333',
  },
  inputForm: {
    display: 'flex',
    marginTop: '15px',
    gap: '10px',
  },
  messageInput: {
    flex: 1,
    padding: '12px',
    borderRadius: '20px',
    border: '1px solid #ccc',
    fontSize: '1em',
    outline: 'none',
    transition: 'border 0.3s ease, box-shadow 0.3s ease',
  },
  sendButton: {
    padding: '12px 20px',
    fontSize: '1em',
    backgroundColor: '#0078d4',
    color: 'white',
    border: 'none',
    borderRadius: '20px',
    cursor: 'pointer',
    transition: 'background 0.2s ease, transform 0.2s ease',
  },
  dateButton: {
    padding: '0 15px',
    fontSize: '1.3em',
    backgroundColor: '#f3f3f3',
    color: '#333',
    border: '1px solid #ccc',
    borderRadius: '20px',
    cursor: 'pointer',
    transition: 'background 0.2s ease, transform 0.2s ease',
  },
  typingIndicator: {
    alignSelf: 'flex-start',
    backgroundColor: '#eaeaea',
    padding: '10px 15px',
    borderRadius: '20px',
    fontSize: '0.9em',
    color: '#555',
    fontStyle: 'italic',
  },
  newChatButton: {
    padding: '10px 20px',
    fontSize: '1em',
    backgroundColor: '#28a745',
    color: 'white',
    border: 'none',
    borderRadius: '5px',
    cursor: 'pointer',
    transition: 'background 0.3s, transform 0.2s',
  },
  chatLog: {
    flex: 1,
    overflowY: 'auto',
    maxHeight: '400px',
    padding: '10px',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  messageWrapper: {
    display: 'flex',
    alignItems: 'flex-end',
    gap: '10px',
    transition: 'background-color 0.3s ease, box-shadow 0.3s ease',
    borderRadius: '24px',
    padding: '4px 8px',
  },
  userWrapper: {
    alignSelf: 'flex-end',
    flexDirection: 'row-reverse',
    cursor: 'default',
  },
  botWrapper: {
    alignSelf: 'flex-start',
    cursor: 'default',
  },
  avatar: {
    width: '36px',
    height: '36px',
    borderRadius: '50%',
    backgroundColor: '#0078d4',
    color: 'white',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    fontSize: '20px',
    userSelect: 'none',
    flexShrink: 0,
    boxShadow: '0 0 6px rgba(0,120,212,0.5)',
  },
  message: {
    padding: '10px 15px',
    borderRadius: '20px',
    maxWidth: '75%',
    fontSize: '0.95em',
    lineHeight: '1.4',
    wordBreak: 'break-word',
    transition: 'background-color 0.3s ease, box-shadow 0.3s ease, transform 0.15s ease',
  },
  user: {
    backgroundColor: '#daf1ff',
    color: '#000',
    borderTopRightRadius: '0px',
  },
  bot: {
    backgroundColor: '#eaeaea',
    color: '#000',
    borderTopLeftRadius: '0px',
  },
  dateInput: {
    padding: '10px',
    fontSize: '1em',
    marginTop: '8px',
    borderRadius: '6px',
    border: '1px solid #ccc',
    outline: 'none',
    transition: 'border-color 0.3s ease, box-shadow 0.3s ease',
  },

};

export default DoctorChat;
