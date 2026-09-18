"use client";
import React, { useState, useEffect } from 'react';
import { inboxApi, InboxConversation, InboxMessage } from '@/lib/api/inbox';

export function UnifiedInbox() {
  const [conversations, setConversations] = useState<InboxConversation[]>([]);
  const [selectedConvo, setSelectedConvo] = useState<InboxConversation | null>(null);
  const [messages, setMessages] = useState<InboxMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [replyText, setReplyText] = useState("");
  const [sending, setSending] = useState(false);

  useEffect(() => {
    fetchConversations();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchConversations = async () => {
    try {
      setLoading(true);
      const data = await inboxApi.getConversations();
      setConversations(data);
      if (data[0]) {
        handleSelectConvo(data[0]);
      }
    } catch (error) {
      console.error('Failed to load conversations', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectConvo = async (convo: InboxConversation) => {
    setSelectedConvo(convo);
    try {
      setMessagesLoading(true);
      const msgs = await inboxApi.getMessages(convo.id);
      setMessages(msgs);
    } catch (error) {
      console.error('Failed to load messages', error);
    } finally {
      setMessagesLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!selectedConvo || !replyText.trim()) return;
    try {
      setSending(true);
      const newMsg = await inboxApi.sendMessage(selectedConvo.id, replyText);
      setMessages([...messages, newMsg]);
      setReplyText("");
    } catch (error) {
      console.error('Failed to send message', error);
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-gray-500">Loading inbox...</div>;
  }

  return (
    <div className="flex h-[calc(100vh-120px)] border border-gray-200 rounded-xl overflow-hidden bg-white shadow-sm font-sans">
      {/* Sidebar: Conversation List */}
      <div className="w-1/3 border-r border-gray-200 bg-gray-50 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <input type="text" placeholder="Search conversations..." className="w-full border border-gray-300 rounded-lg p-2 text-sm focus:ring-indigo-500 focus:border-indigo-500" />
        </div>
        <div className="flex-1 overflow-y-auto">
          {conversations.length === 0 ? (
            <div className="p-4 text-sm text-gray-500 text-center">No conversations found.</div>
          ) : (
            conversations.map(convo => (
              <div 
                key={convo.id} 
                onClick={() => handleSelectConvo(convo)}
                className={`p-4 border-b border-gray-100 cursor-pointer transition-colors ${selectedConvo?.id === convo.id ? 'bg-indigo-50' : 'hover:bg-gray-100'}`}
              >
                <div className="flex justify-between items-start mb-1">
                  <span className="font-semibold text-gray-900 truncate">
                    {convo.contact_name || convo.channel_identity || convo.contact_id || 'Unknown Contact'}
                  </span>
                  <span className="text-xs text-gray-500">
                    {new Date(convo.updated_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm truncate text-gray-500">{convo.status}</span>
                  <span className="text-xs px-2 py-1 bg-gray-200 text-gray-700 rounded-full">{convo.channel}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="w-2/3 flex flex-col bg-white">
        {selectedConvo ? (
          <>
            {/* Header */}
            <div className="p-4 border-b border-gray-200 flex justify-between items-center">
              <div>
                <h2 className="text-lg font-bold text-gray-900">
                  {selectedConvo.contact_name || selectedConvo.channel_identity || selectedConvo.contact_id || 'Unknown Contact'}
                </h2>
                <p className="text-sm text-gray-500">via {selectedConvo.channel}</p>
              </div>
              <button className="text-sm bg-white border border-gray-300 text-gray-700 py-1.5 px-3 rounded-md hover:bg-gray-50">
                Resolve
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 p-6 overflow-y-auto space-y-4 bg-gray-50">
              {messagesLoading ? (
                <div className="text-center text-sm text-gray-500">Loading messages...</div>
              ) : messages.length === 0 ? (
                <div className="text-center text-sm text-gray-500">No messages yet.</div>
              ) : (
                messages.map(msg => (
                  <div key={msg.id} className={`flex ${msg.direction === 'OUTBOUND' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`border p-3 rounded-2xl max-w-[75%] shadow-sm ${msg.direction === 'OUTBOUND' ? 'bg-indigo-600 border-indigo-600 text-white rounded-tr-none' : 'bg-white border-gray-200 text-gray-800 rounded-tl-none'}`}>
                      <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                      <p className={`text-xs mt-1 ${msg.direction === 'OUTBOUND' ? 'text-indigo-200' : 'text-gray-400'}`}>
                        {new Date(msg.created_at).toLocaleTimeString()} · {msg.status}
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Input */}
            <div className="p-4 border-t border-gray-200 bg-white">
              <div className="flex items-center gap-2">
                <textarea 
                  className="flex-1 border border-gray-300 rounded-lg p-2 text-sm focus:ring-indigo-500 focus:border-indigo-500 resize-none disabled:opacity-50" 
                  rows={2} 
                  placeholder={`Reply via ${selectedConvo.channel}...`}
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  disabled={sending}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage();
                    }
                  }}
                />
                <button 
                  onClick={handleSendMessage}
                  disabled={sending || !replyText.trim()}
                  className="bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-300 text-white p-3 rounded-lg flex-shrink-0 transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                </button>
              </div>
              {selectedConvo.channel === 'WHATSAPP' && (
                <p className="text-xs text-gray-500 mt-2">You are within the 24-hour service window to reply freely.</p>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            Select a conversation to view
          </div>
        )}
      </div>
    </div>
  );
}
