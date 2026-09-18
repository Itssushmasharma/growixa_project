"use client";
import React from 'react';

export function AutomationBuilder() {

  return (
    <div className="flex flex-col h-screen bg-gray-50 p-6 font-sans">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Automation Builder</h1>
          <p className="text-gray-500 mt-1">Design workflows visually with triggers, conditions, and actions.</p>
        </div>
        <button className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded-lg shadow">
          Save Workflow
        </button>
      </div>

      <div className="flex-1 bg-white border border-gray-200 rounded-xl shadow-sm p-8 flex flex-col items-center relative overflow-hidden">
        {/* Placeholder Node Graph */}
        <div className="flex flex-col items-center gap-6">
          <div className="bg-indigo-50 border-2 border-indigo-200 w-64 p-4 rounded-xl shadow-sm relative text-center">
            <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider mb-2 block">Trigger</span>
            <div className="font-semibold text-gray-800">New Contact Created</div>
          </div>
          
          <div className="w-px h-8 bg-gray-300"></div>

          <div className="bg-amber-50 border-2 border-amber-200 w-64 p-4 rounded-xl shadow-sm relative text-center">
            <span className="text-xs font-bold text-amber-600 uppercase tracking-wider mb-2 block">Condition</span>
            <div className="font-semibold text-gray-800">Source == &apos;Website&apos;</div>
          </div>

          <div className="w-px h-8 bg-gray-300"></div>

          <div className="bg-emerald-50 border-2 border-emerald-200 w-64 p-4 rounded-xl shadow-sm relative text-center">
            <span className="text-xs font-bold text-emerald-600 uppercase tracking-wider mb-2 block">Action</span>
            <div className="font-semibold text-gray-800">Add Tag: Hot Lead</div>
          </div>
          
          <button className="mt-4 w-12 h-12 bg-gray-100 hover:bg-gray-200 rounded-full flex items-center justify-center text-gray-600 border border-gray-300 text-xl font-light transition-colors">
            +
          </button>
        </div>
      </div>
    </div>
  );
}
