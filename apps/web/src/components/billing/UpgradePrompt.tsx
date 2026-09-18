"use client";
import React from 'react';
import Link from 'next/link';

interface UpgradePromptProps {
  isOpen: boolean;
  onClose: () => void;
  featureName: string;
}

export function UpgradePrompt({ isOpen, onClose, featureName }: UpgradePromptProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-gray-900/50 backdrop-blur-sm transition-opacity">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200">
        <div className="p-6 text-center">
          <div className="w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-gray-900 tracking-tight mb-2">
            Unlock {featureName}
          </h2>
          <p className="text-gray-500 mb-6">
            This feature is available on the Growth plan. Upgrade today to scale your agency and access advanced tools.
          </p>
          <div className="flex flex-col gap-3">
            <Link 
              href="/dashboard/billing" 
              onClick={onClose}
              className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 px-4 rounded-xl shadow-sm transition-all hover:shadow"
            >
              Upgrade to Growth
            </Link>
            <button 
              onClick={onClose} 
              className="w-full text-gray-500 hover:text-gray-900 font-medium py-3 px-4"
            >
              Maybe later
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
