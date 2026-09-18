"use client";
import React, { useState } from 'react';

const mockPosts = [
  { id: 1, title: 'Summer Campaign Launch', platform: 'Instagram', status: 'PENDING_APPROVAL', author: 'Jane Smith', date: 'Oct 2, 2026' },
  { id: 2, title: 'Weekly Tech Tips', platform: 'LinkedIn', status: 'DRAFT', author: 'John Doe', date: 'Oct 3, 2026' },
  { id: 3, title: 'New Feature Announcement', platform: 'Twitter', status: 'APPROVED', author: 'Jane Smith', date: 'Oct 5, 2026' },
  { id: 4, title: 'Behind the Scenes Office', platform: 'Facebook', status: 'REJECTED', author: 'John Doe', date: 'Oct 1, 2026' },
];

export default function ApprovalsPage() {
  const [filter, setFilter] = useState('ALL');

  const filteredPosts = filter === 'ALL' ? mockPosts : mockPosts.filter(p => p.status === filter);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Approvals</h1>
          <p className="mt-2 text-sm text-gray-500">
            Collaborate with your clients and team to review and approve content before publishing.
          </p>
        </div>
        <button className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg font-medium shadow-sm transition-colors">
          Create Draft
        </button>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {['ALL', 'DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED'].map(tab => (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              className={`${
                filter === tab
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
            >
              {tab.replace('_', ' ')}
            </button>
          ))}
        </nav>
      </div>

      {/* List */}
      <div className="bg-white shadow-sm border border-gray-200 rounded-xl overflow-hidden">
        <ul className="divide-y divide-gray-200">
          {filteredPosts.map(post => (
            <li key={post.id} className="p-6 hover:bg-gray-50 transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex flex-col">
                  <div className="flex items-center gap-3">
                    <h3 className="text-sm font-bold text-gray-900">{post.title}</h3>
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium 
                      ${post.status === 'APPROVED' ? 'bg-green-100 text-green-800' : 
                        post.status === 'PENDING_APPROVAL' ? 'bg-yellow-100 text-yellow-800' : 
                        post.status === 'REJECTED' ? 'bg-red-100 text-red-800' : 
                        'bg-gray-100 text-gray-800'}`}>
                      {post.status.replace('_', ' ')}
                    </span>
                  </div>
                  <div className="mt-2 text-sm text-gray-500 flex items-center gap-4">
                    <span>{post.platform}</span>
                    <span>•</span>
                    <span>By {post.author}</span>
                    <span>•</span>
                    <span>Scheduled: {post.date}</span>
                  </div>
                </div>
                
                <div className="flex items-center gap-3">
                  {post.status === 'PENDING_APPROVAL' && (
                    <>
                      <button className="text-green-600 hover:text-green-900 text-sm font-medium border border-green-200 bg-green-50 px-3 py-1.5 rounded">Approve</button>
                      <button className="text-red-600 hover:text-red-900 text-sm font-medium border border-red-200 bg-red-50 px-3 py-1.5 rounded">Reject</button>
                    </>
                  )}
                  <button className="text-indigo-600 hover:text-indigo-900 text-sm font-medium">Review</button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
