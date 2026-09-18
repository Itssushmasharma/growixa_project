"use client";
import React, { useState } from 'react';
import { apiFetch } from "@/lib/api-client";
import { useToast } from "@/components/toast/toast-context";

export function AutomationBuilder() {
  const { showToast } = useToast();
  const [trigger, setTrigger] = useState("contact.created");
  const [actions, setActions] = useState([{ type: "add_tag", tag: "" }]);
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    setSaving(true);
    try {
      await apiFetch("/automations", {
        method: "POST",
        body: JSON.stringify({
          name: "New Automation Workflow",
          trigger_type: trigger,
          conditions: [],
          actions: actions.map(a => ({ type: a.type, config: { tag: a.tag } }))
        })
      });
      showToast("success", "Workflow saved successfully!");
    } catch (e) {
      showToast("error", "Failed to save workflow.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="p-8 max-w-4xl mx-auto font-sans text-gray-900 bg-gray-50 min-h-screen">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Workflow Builder</h1>
          <p className="text-gray-500 mt-2">Design cross-channel automations using triggers and actions.</p>
        </div>
        <button 
          onClick={handleSave}
          disabled={saving}
          className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-2 px-4 rounded-md shadow-sm disabled:opacity-50"
        >
          {saving ? "Saving..." : "Save Workflow"}
        </button>
      </div>

      <div className="space-y-6 flex flex-col items-center">
        {/* Trigger Node */}
        <div className="bg-white border-2 border-indigo-200 shadow-sm rounded-xl p-6 w-full max-w-md">
          <div className="flex items-center gap-3 border-b border-gray-100 pb-3 mb-4">
            <div className="bg-indigo-100 text-indigo-700 p-2 rounded-lg">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="font-semibold text-lg">Trigger</h3>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">When this happens:</label>
            <select 
              value={trigger} 
              onChange={e => setTrigger(e.target.value)}
              className="w-full border border-gray-300 rounded-md shadow-sm p-2 text-sm focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="contact.created">New Contact Added</option>
              <option value="segment.entered">Contact Enters Segment</option>
              <option value="email.opened">Email Opened</option>
            </select>
          </div>
        </div>

        {/* Connector Line */}
        <div className="w-0.5 h-8 bg-gray-300"></div>

        {/* Action Nodes */}
        {actions.map((action, index) => (
          <div key={index} className="bg-white border border-gray-200 shadow-sm rounded-xl p-6 w-full max-w-md relative">
            <div className="flex items-center gap-3 border-b border-gray-100 pb-3 mb-4">
              <div className="bg-green-100 text-green-700 p-2 rounded-lg">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </div>
              <h3 className="font-semibold text-lg">Action</h3>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Do this:</label>
                <select 
                  value={action.type}
                  onChange={(e) => {
                    const newActions = [...actions];
                    if (newActions[index]) {
                      newActions[index] = { ...newActions[index], type: e.target.value };
                      setActions(newActions);
                    }
                  }}
                  className="w-full border border-gray-300 rounded-md shadow-sm p-2 text-sm focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="add_tag">Add Tag to Contact</option>
                  <option value="send_email">Send Email Campaign</option>
                  <option value="send_whatsapp">Send WhatsApp Message</option>
                </select>
              </div>

              {action.type === 'add_tag' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tag Name</label>
                  <input type="text" className="w-full border border-gray-300 rounded-md shadow-sm p-2 text-sm focus:ring-indigo-500 focus:border-indigo-500" placeholder="e.g. vip-lead" />
                </div>
              )}
              {action.type === 'send_email' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Select Email Template</label>
                  <select className="w-full border border-gray-300 rounded-md shadow-sm p-2 text-sm focus:ring-indigo-500 focus:border-indigo-500">
                    <option>Welcome Series - Email 1</option>
                  </select>
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Add Node Button */}
        <div className="w-0.5 h-8 bg-gray-300"></div>
        <button 
          onClick={() => setActions([...actions, { type: "add_tag", tag: "" }])}
          className="flex items-center justify-center w-10 h-10 rounded-full bg-white border-2 border-dashed border-gray-300 text-gray-500 hover:text-indigo-600 hover:border-indigo-600 transition-colors"
        >
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </button>
      </div>
    </div>
  );
}
