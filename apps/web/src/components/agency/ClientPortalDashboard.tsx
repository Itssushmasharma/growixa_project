"use client";
import React from 'react';

export function ClientPortalDashboard() {
  // In a real app, these values would come from WhiteLabelConfig in the DB
  const agencyTheme = {
    primaryColor: '#0ea5e9', // Sky Blue
    logoText: 'GrowthMasters',
    portalName: 'Client Access Portal'
  };

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900">
      
      {/* White-labeled Header */}
      <header className="bg-white border-b border-slate-200 shadow-sm p-4 flex justify-between items-center" style={{ borderTop: `4px solid ${agencyTheme.primaryColor}` }}>
        <div className="flex items-center gap-3">
          {/* Mock Logo */}
          <div 
            className="w-8 h-8 rounded-md flex items-center justify-center text-white font-bold text-lg"
            style={{ backgroundColor: agencyTheme.primaryColor }}
          >
            G
          </div>
          <span className="font-bold text-lg">{agencyTheme.logoText} <span className="text-slate-400 font-normal">| {agencyTheme.portalName}</span></span>
        </div>
        <div className="flex gap-4">
          <span className="text-sm text-slate-500 font-medium">Logged in as: TechCorp Admin</span>
        </div>
      </header>

      <main className="max-w-5xl mx-auto p-8 mt-8">
        
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Pending Approvals</h1>
          <p className="text-slate-500">Review content created by your agency team.</p>
        </div>

        {/* Approval Cards */}
        <div className="space-y-4">
          
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex gap-6">
            <div className="w-48 h-48 bg-slate-100 rounded-lg border border-slate-200 flex items-center justify-center shrink-0">
              <span className="text-slate-400 text-sm">Image Placeholder</span>
            </div>
            <div className="flex-1 flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-start">
                  <div>
                    <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider bg-indigo-50 px-2 py-1 rounded">Instagram Post</span>
                    <h3 className="font-bold text-lg mt-2">Q4 Product Launch Announcement</h3>
                  </div>
                  <span className="text-sm text-slate-500">Scheduled: Oct 15</span>
                </div>
                <p className="mt-4 text-slate-700 whitespace-pre-wrap">
                  Get ready for the biggest update of the year! 🚀\nOur new features are designed to help you scale faster. Link in bio!
                </p>
              </div>
              
              <div className="flex justify-end gap-3 mt-6 border-t border-slate-100 pt-4">
                <button className="px-4 py-2 border border-slate-300 rounded-lg text-sm font-semibold hover:bg-slate-50">
                  Request Changes
                </button>
                <button 
                  className="px-4 py-2 text-white rounded-lg text-sm font-semibold transition-opacity hover:opacity-90 shadow-sm"
                  style={{ backgroundColor: agencyTheme.primaryColor }}
                >
                  Approve Content
                </button>
              </div>
            </div>
          </div>
          
        </div>
      </main>
    </div>
  );
}
