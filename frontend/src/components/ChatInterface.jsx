import React, { useState } from 'react';
import { Send, Bot, User, Sparkles, Loader2 } from 'lucide-react';
import { sendChatMessage } from '../services/api';

export const ChatInterface = () => {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I am your AI Shopping Assistant. Tell me what you are looking for—for example, "Find organic honey under $20 with at least 4.5 stars" or upload an image to search.'
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const suggestedPrompts = [
    "Find organic honey under $20.",
    "Show products rated at least 4.5 stars.",
    "Recommend healthy snacks under $10.",
    "Compare organic almonds and cashews."
  ];

  const handleSend = async (textToSend) => {
    const text = textToSend || input;
    if (!text.trim() || loading) return;

    const newMessages = [...messages, { role: 'user', content: text }];
    setMessages(newMessages);
    setInput('');
    setLoading(true);

    try {
      const res = await sendChatMessage(newMessages.map(m => ({ role: m.role, content: m.content })));
      setMessages(res.session_messages);
    } catch (err) {
      setMessages([...newMessages, { role: 'assistant', content: 'Sorry, I encountered an error communicating with the AI service. Please verify your Groq API key configuration.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 flex flex-col h-[calc(100vh-12rem)]">
      <div className="p-4 border-b border-gray-100 flex items-center space-x-3 bg-gray-50 rounded-t-xl">
        <div className="w-9 h-9 rounded-full bg-indigo-600 text-white flex items-center justify-center shadow-sm">
          <Bot className="w-5 h-5" />
        </div>
        <div>
          <h2 className="font-semibold text-gray-900">AI Shopping Assistant</h2>
          <p className="text-xs text-gray-500">Powered by Groq & LangChain Agent</p>
        </div>
      </div>

      <div className="p-3 bg-indigo-50/50 border-b border-indigo-100/50 flex flex-wrap gap-2 items-center">
        <span className="text-xs font-semibold text-indigo-700 flex items-center space-x-1">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Suggestions:</span>
        </span>
        {suggestedPrompts.map((prompt, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(prompt)}
            className="text-xs bg-white text-indigo-700 hover:bg-indigo-600 hover:text-white px-2.5 py-1 rounded-full border border-indigo-200 transition-colors shadow-sm"
          >
            {prompt}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, index) => (
          <div key={index} className={`flex items-start space-x-3 ${msg.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'user' ? 'bg-gray-800 text-white' : 'bg-indigo-600 text-white'}`}>
              {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>
            <div className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm ${msg.role === 'user' ? 'bg-gray-900 text-white rounded-tr-none' : 'bg-gray-100 text-gray-800 rounded-tl-none whitespace-pre-line'}`}>
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex items-start space-x-3">
            <div className="w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center flex-shrink-0">
              <Bot className="w-4 h-4" />
            </div>
            <div className="bg-gray-100 text-gray-500 rounded-2xl rounded-tl-none px-4 py-3 text-sm flex items-center space-x-2">
              <Loader2 className="w-4 h-4 animate-spin text-indigo-600" />
              <span>Thinking and searching store...</span>
            </div>
          </div>
        )}
      </div>

      <div className="p-4 border-t border-gray-100 bg-white rounded-b-xl">
        <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about products, prices, ratings, or order..."
            className="flex-1 px-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white px-5 py-3 rounded-xl font-medium transition-colors flex items-center justify-center shadow-sm"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  );
};
