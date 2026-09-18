"use client";
import React, { useState, useEffect } from 'react';

export function WelcomeModal() {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    // Show only on first login (mocked by checking session storage)
    const hasSeen = sessionStorage.getItem('growixa_welcome_seen');
    if (!hasSeen) {
      setIsOpen(true);
    }
  }, []);

  const handleClose = () => {
    sessionStorage.setItem('growixa_welcome_seen', 'true');
    setIsOpen(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/40 backdrop-blur-sm transition-opacity">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in duration-300">
        <div className="bg-gradient-to-r from-indigo-500 to-purple-600 p-8 text-center">
          <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg">
            <svg className="w-8 h-8 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Welcome to Growixa!</h2>
          <p className="text-indigo-100 mt-2">Your agency's growth engine is ready to go.</p>
        </div>
        <div className="p-6">
          <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider mb-4">Quick Start Guide</h3>
          <ul className="space-y-4">
            <li className="flex items-start">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold text-xs mt-0.5">1</div>
              <div className="ml-3">
                <p className="text-sm font-semibold text-gray-900">Connect Social Accounts</p>
                <p className="text-sm text-gray-500">Link your client's Instagram, LinkedIn, or Twitter.</p>
              </div>
            </li>
            <li className="flex items-start">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold text-xs mt-0.5">2</div>
              <div className="ml-3">
                <p className="text-sm font-semibold text-gray-900">Setup White-Label Portal</p>
                <p className="text-sm text-gray-500">Customize the dashboard with your agency branding.</p>
              </div>
            </li>
            <li className="flex items-start">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold text-xs mt-0.5">3</div>
              <div className="ml-3">
                <p className="text-sm font-semibold text-gray-900">Schedule First Post</p>
                <p className="text-sm text-gray-500">Use AI or templates to draft your first campaign.</p>
              </div>
            </li>
          </ul>
          <div className="mt-8 pt-6 border-t border-gray-100 flex gap-4">
            <button onClick={handleClose} className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold py-2.5 rounded-xl transition-colors">
              I&apos;ll explore myself
            </button>
            <button onClick={handleClose} className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2.5 rounded-xl shadow-sm transition-all hover:shadow">
              Get Started
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
