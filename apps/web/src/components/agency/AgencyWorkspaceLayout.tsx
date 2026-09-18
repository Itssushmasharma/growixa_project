"use client";
import React, { useState } from 'react';

export function AgencyWorkspaceLayout({ children }: { children: React.ReactNode }) {
  const [activeClient, setActiveClient] = useState("TechCorp Inc.");

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col font-sans text-gray-900">
      
      {/* Global Agency Header */}
      <header className="bg-gray-900 text-white p-4 flex justify-between items-center">
        <div className="flex items-center gap-4">
          <div className="font-bold text-xl tracking-tight">GrowthMasters Agency</div>
          <div className="h-6 w-px bg-gray-700 mx-2"></div>
          
          {/* Client Switcher Dropdown Placeholder */}
          <div className="relative">
            <select 
              className="bg-gray-800 border border-gray-700 text-white rounded-md pl-3 pr-8 py-1.5 text-sm appearance-none focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={activeClient}
              onChange={(e) => setActiveClient(e.target.value)}
            >
              <option value="TechCorp Inc.">TechCorp Inc.</option>
              <option value="Acme Sneakers">Acme Sneakers</option>
              <option value="Local Coffee Shop">Local Coffee Shop</option>
            </select>
          </div>
        </div>

        <div className="flex gap-4 text-sm font-medium">
          <button className="text-gray-300 hover:text-white">Agency Settings</button>
          <button className="text-gray-300 hover:text-white">Team</button>
          <button className="text-gray-300 hover:text-white">Billing (Stripe)</button>
        </div>
      </header>

      {/* Client Context Banner */}
      <div className="bg-blue-600 text-white px-6 py-2 text-sm font-medium flex justify-between">
        <span>Currently managing: <span className="font-bold">{activeClient}</span></span>
        <button className="bg-blue-700 hover:bg-blue-800 px-3 py-1 rounded text-xs transition-colors">
          View as Client
        </button>
      </div>

      {/* Main Workspace Area */}
      <main className="flex-1 p-8">
        <div className="max-w-7xl mx-auto">
          {children || (
            <div className="bg-white border border-gray-200 rounded-xl p-12 text-center shadow-sm">
              <h2 className="text-2xl font-bold mb-2">Welcome to the Workspace for {activeClient}</h2>
              <p className="text-gray-500">Any content created here is strictly isolated to this client&apos;s account.</p>
            </div>
          )}
        </div>
      </main>

    </div>
  );
}
