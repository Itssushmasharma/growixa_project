"use client";
import React from 'react';

export function UnifiedAnalyticsDashboard() {
  return (
    <div className="p-8 max-w-6xl mx-auto font-sans text-gray-900 bg-gray-50 min-h-screen">
      <div className="flex justify-between items-end mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Unified Analytics</h1>
          <p className="text-gray-500 mt-1">Cross-channel intelligence and reporting.</p>
        </div>
        <div className="flex gap-4">
          <select className="border border-gray-300 rounded-lg p-2 bg-white text-sm">
            <option>Last 30 Days</option>
            <option>This Month</option>
            <option>This Quarter</option>
          </select>
          <button className="bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 font-semibold py-2 px-4 rounded-lg shadow-sm">
            Export PDF
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <p className="text-sm text-gray-500 font-medium">Total Audience Growth</p>
          <div className="mt-2 flex items-baseline gap-2">
            <p className="text-3xl font-bold">12,450</p>
            <p className="text-sm text-emerald-600 font-semibold">↑ 14%</p>
          </div>
        </div>
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <p className="text-sm text-gray-500 font-medium">Email Open Rate</p>
          <div className="mt-2 flex items-baseline gap-2">
            <p className="text-3xl font-bold">24.8%</p>
            <p className="text-sm text-emerald-600 font-semibold">↑ 2.1%</p>
          </div>
        </div>
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <p className="text-sm text-gray-500 font-medium">Social Engagement</p>
          <div className="mt-2 flex items-baseline gap-2">
            <p className="text-3xl font-bold">8,204</p>
            <p className="text-sm text-emerald-600 font-semibold">↑ 34%</p>
          </div>
        </div>
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <p className="text-sm text-gray-500 font-medium">New CRM Leads</p>
          <div className="mt-2 flex items-baseline gap-2">
            <p className="text-3xl font-bold">342</p>
            <p className="text-sm text-red-500 font-semibold">↓ 5%</p>
          </div>
        </div>
      </div>

      {/* Main Charts Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-gray-200 shadow-sm h-96 flex flex-col">
          <h2 className="text-lg font-bold mb-4">Audience Growth (Cross-Channel)</h2>
          <div className="flex-1 bg-gray-50 rounded-lg border border-dashed border-gray-300 flex items-center justify-center">
            <p className="text-gray-400">[ Recharts LineGraph Placeholder ]</p>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm h-96 flex flex-col">
          <h2 className="text-lg font-bold mb-4">Traffic Sources</h2>
          <div className="flex-1 bg-gray-50 rounded-lg border border-dashed border-gray-300 flex items-center justify-center">
            <p className="text-gray-400">[ Recharts DonutChart Placeholder ]</p>
          </div>
        </div>
      </div>
    </div>
  );
}
