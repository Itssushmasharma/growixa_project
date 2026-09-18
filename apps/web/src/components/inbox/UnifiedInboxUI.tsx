"use client";
import React from 'react';

export function UnifiedInboxUI() {
  return (
    <div className="flex h-screen bg-gray-50 font-sans text-gray-900 overflow-hidden">
      
      {/* Left Sidebar - Conversations List */}
      <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200 bg-gray-50 flex items-center justify-between">
          <h2 className="font-bold text-lg">Inbox</h2>
          <span className="bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded-full font-semibold">12 New</span>
        </div>
        
        {/* Filters */}
        <div className="flex p-2 gap-2 border-b border-gray-200 text-sm">
          <button className="flex-1 bg-gray-100 py-1 rounded-md font-medium text-gray-800">All</button>
          <button className="flex-1 text-gray-500 hover:bg-gray-100 rounded-md">Unread</button>
          <button className="flex-1 text-gray-500 hover:bg-gray-100 rounded-md">Assigned</button>
        </div>

        {/* Conversation List */}
        <div className="flex-1 overflow-y-auto">
          {/* Item 1 */}
          <div className="p-4 border-b border-gray-100 hover:bg-gray-50 cursor-pointer bg-blue-50/30">
            <div className="flex justify-between items-start mb-1">
              <span className="font-semibold text-sm">John Doe</span>
              <span className="text-xs text-gray-400">10:42 AM</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs px-1.5 py-0.5 rounded bg-green-100 text-green-700 font-bold border border-green-200">WA</span>
              <p className="text-sm text-gray-600 truncate">Hey, I&apos;m interested in the new pricing plan...</p>
            </div>
          </div>

          {/* Item 2 */}
          <div className="p-4 border-b border-gray-100 hover:bg-gray-50 cursor-pointer">
            <div className="flex justify-between items-start mb-1">
              <span className="font-semibold text-sm">TechCorp Inc.</span>
              <span className="text-xs text-gray-400">Yesterday</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 font-bold border border-blue-200">Email</span>
              <p className="text-sm text-gray-600 truncate">Following up on our meeting...</p>
            </div>
          </div>
          
           {/* Item 3 */}
           <div className="p-4 border-b border-gray-100 hover:bg-gray-50 cursor-pointer">
            <div className="flex justify-between items-start mb-1">
              <span className="font-semibold text-sm">@sarah_codes</span>
              <span className="text-xs text-gray-400">Tuesday</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs px-1.5 py-0.5 rounded bg-pink-100 text-pink-700 font-bold border border-pink-200">IG</span>
              <p className="text-sm text-gray-600 truncate">Love this new feature! 🔥</p>
            </div>
          </div>
        </div>
      </div>

      {/* Middle Pane - Chat History */}
      <div className="flex-1 flex flex-col bg-white">
        {/* Header */}
        <div className="p-4 border-b border-gray-200 flex justify-between items-center bg-white">
          <div>
            <h3 className="font-bold text-lg">John Doe</h3>
            <p className="text-sm text-gray-500">via WhatsApp Business</p>
          </div>
          <div className="flex gap-2">
            <button className="text-sm border border-gray-300 px-3 py-1.5 rounded-lg font-medium hover:bg-gray-50">Mark Done</button>
            <button className="text-sm border border-gray-300 px-3 py-1.5 rounded-lg font-medium hover:bg-gray-50">Assign</button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 p-6 overflow-y-auto bg-gray-50 space-y-4">
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 p-3 rounded-2xl rounded-tl-sm max-w-md shadow-sm">
              <p className="text-sm">Hey, I&apos;m interested in the new pricing plan. Can you share more details?</p>
              <p className="text-xs text-gray-400 mt-1 text-right">10:42 AM</p>
            </div>
          </div>
        </div>

        {/* Input */}
        <div className="p-4 bg-white border-t border-gray-200">
          <div className="border border-gray-300 rounded-xl overflow-hidden focus-within:ring-2 focus-within:ring-blue-500">
            <textarea className="w-full p-3 outline-none resize-none" rows={3} placeholder="Type a reply..."></textarea>
            <div className="bg-gray-50 px-3 py-2 flex justify-between items-center border-t border-gray-200">
              <button className="text-gray-500 hover:text-gray-700">📎 Attach</button>
              <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-1.5 rounded-lg font-semibold text-sm">Send Reply</button>
            </div>
          </div>
        </div>
      </div>

      {/* Right Sidebar - CRM Context */}
      <div className="w-80 bg-white border-l border-gray-200 p-6 overflow-y-auto">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center text-xl font-bold text-gray-500">JD</div>
          <div>
            <h3 className="font-bold text-lg">John Doe</h3>
            <p className="text-sm text-gray-500">Marketing Lead</p>
          </div>
        </div>
        
        <div className="mb-6">
          <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">CRM Profile</h4>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between"><span className="text-gray-500">Stage</span><span className="font-medium text-blue-600 bg-blue-50 px-2 py-0.5 rounded">SQL</span></div>
            <div className="flex justify-between"><span className="text-gray-500">Company</span><span className="font-medium text-gray-900">Acme Corp</span></div>
            <div className="flex justify-between"><span className="text-gray-500">Phone</span><span className="font-medium text-gray-900">+1 234 567 8900</span></div>
            <div className="flex justify-between"><span className="text-gray-500">Email</span><span className="font-medium text-gray-900">john@acme.com</span></div>
          </div>
        </div>

        <div>
          <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Recent Activity</h4>
          <ul className="space-y-4 relative before:absolute before:inset-0 before:ml-2 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-gray-300 before:to-transparent">
            <li className="relative flex items-center gap-3">
              <div className="w-4 h-4 rounded-full bg-blue-500 shrink-0 z-10 border-2 border-white"></div>
              <div>
                <p className="text-sm text-gray-800">Opened Email Campaign</p>
                <p className="text-xs text-gray-500">2 days ago</p>
              </div>
            </li>
            <li className="relative flex items-center gap-3">
              <div className="w-4 h-4 rounded-full bg-green-500 shrink-0 z-10 border-2 border-white"></div>
              <div>
                <p className="text-sm text-gray-800">Visited Pricing Page</p>
                <p className="text-xs text-gray-500">4 days ago</p>
              </div>
            </li>
          </ul>
        </div>
      </div>

    </div>
  );
}
