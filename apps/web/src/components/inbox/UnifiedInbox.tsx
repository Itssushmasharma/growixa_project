"use client";
import React, { useState } from 'react';

const mockConversations = [
  { id: 1, channel: 'WHATSAPP', contact: 'John Doe', lastMessage: 'Is the product available?', time: '10:42 AM', unread: true },
  { id: 2, channel: 'SOCIAL', contact: '@tech_guru', lastMessage: 'Great new feature!', time: 'Yesterday', unread: false },
  { id: 3, channel: 'EMAIL', contact: 'jane@example.com', lastMessage: 'I would like to request a demo.', time: 'Oct 12', unread: false },
];

export function UnifiedInbox() {
  const [selectedConvo, setSelectedConvo] = useState(mockConversations[0]);

  return (
    <div className="flex h-[calc(100vh-120px)] border border-gray-200 rounded-xl overflow-hidden bg-white shadow-sm font-sans">
      {/* Sidebar: Conversation List */}
      <div className="w-1/3 border-r border-gray-200 bg-gray-50 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <input type="text" placeholder="Search conversations..." className="w-full border border-gray-300 rounded-lg p-2 text-sm focus:ring-indigo-500 focus:border-indigo-500" />
        </div>
        <div className="flex-1 overflow-y-auto">
          {mockConversations.map(convo => (
            <div 
              key={convo.id} 
              onClick={() => setSelectedConvo(convo)}
              className={`p-4 border-b border-gray-100 cursor-pointer transition-colors ${selectedConvo?.id === convo.id ? 'bg-indigo-50' : 'hover:bg-gray-100'}`}
            >
              <div className="flex justify-between items-start mb-1">
                <span className="font-semibold text-gray-900">{convo.contact}</span>
                <span className="text-xs text-gray-500">{convo.time}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className={`text-sm truncate ${convo.unread ? 'font-semibold text-gray-800' : 'text-gray-500'}`}>{convo.lastMessage}</span>
                <span className="text-xs px-2 py-1 bg-gray-200 text-gray-700 rounded-full">{convo.channel}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="w-2/3 flex flex-col bg-white">
        {selectedConvo ? (
          <>
            {/* Header */}
            <div className="p-4 border-b border-gray-200 flex justify-between items-center">
              <div>
                <h2 className="text-lg font-bold text-gray-900">{selectedConvo.contact}</h2>
                <p className="text-sm text-gray-500">via {selectedConvo.channel}</p>
              </div>
              <button className="text-sm bg-white border border-gray-300 text-gray-700 py-1.5 px-3 rounded-md hover:bg-gray-50">
                Resolve
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 p-6 overflow-y-auto space-y-4 bg-gray-50">
              <div className="flex justify-start">
                <div className="bg-white border border-gray-200 p-3 rounded-2xl rounded-tl-none max-w-[75%] shadow-sm">
                  <p className="text-sm text-gray-800">{selectedConvo.lastMessage}</p>
                  <p className="text-xs text-gray-400 mt-1">{selectedConvo.time}</p>
                </div>
              </div>
            </div>

            {/* Input */}
            <div className="p-4 border-t border-gray-200 bg-white">
              <div className="flex items-center gap-2">
                <textarea 
                  className="flex-1 border border-gray-300 rounded-lg p-2 text-sm focus:ring-indigo-500 focus:border-indigo-500 resize-none" 
                  rows={2} 
                  placeholder={`Reply to ${selectedConvo.contact}...`}
                />
                <button className="bg-indigo-600 hover:bg-indigo-500 text-white p-3 rounded-lg flex-shrink-0 transition-colors">
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
