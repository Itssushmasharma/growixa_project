"use client";
import React, { useState } from 'react';

type Channel = 'EMAIL' | 'WHATSAPP' | 'SMS';

export function UnifiedCampaignBuilder() {
  const [channel, setChannel] = useState<Channel>('EMAIL');
  const [smsText, setSmsText] = useState("");
  
  const smsLength = smsText.length;
  const smsSegments = Math.ceil((smsLength || 1) / 160);

  return (
    <div className="p-8 max-w-4xl mx-auto font-sans text-gray-900">
      <h1 className="text-3xl font-bold mb-2">Create New Campaign</h1>
      <p className="text-gray-500 mb-8">Select a communication channel to begin.</p>

      {/* Channel Selector */}
      <div className="flex space-x-4 mb-8">
        {(['EMAIL', 'WHATSAPP', 'SMS'] as Channel[]).map((c) => (
          <button
            key={c}
            onClick={() => setChannel(c)}
            className={`flex-1 py-4 px-6 border-2 rounded-xl text-center font-semibold transition-all ${
              channel === c
                ? 'border-blue-600 bg-blue-50 text-blue-700'
                : 'border-gray-200 hover:border-gray-300 text-gray-600'
            }`}
          >
            {c === 'EMAIL' && 'Email Campaign'}
            {c === 'WHATSAPP' && 'WhatsApp Broadcast'}
            {c === 'SMS' && 'SMS Campaign'}
          </button>
        ))}
      </div>

      {/* Dynamic Form Area */}
      <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-6">
        <h2 className="text-xl font-semibold mb-4">
          {channel === 'EMAIL' && 'Email Details'}
          {channel === 'WHATSAPP' && 'WhatsApp Details'}
          {channel === 'SMS' && 'SMS Details'}
        </h2>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Campaign Name</label>
            <input type="text" className="w-full border border-gray-300 rounded-lg p-2" placeholder="e.g. Q4 Promo" />
          </div>

          {channel === 'WHATSAPP' && (
            <div className="bg-amber-50 border border-amber-200 text-amber-800 p-4 rounded-lg">
              <p className="font-semibold">WhatsApp Business Account</p>
              <p className="text-sm">You must select an approved Meta Cloud API template for this broadcast.</p>
              <select className="mt-2 w-full border border-gray-300 rounded-lg p-2">
                <option>Select an approved template...</option>
                <option>Welcome Message (APPROVED)</option>
              </select>
            </div>
          )}

          {channel === 'SMS' && (
            <div className="bg-blue-50 border border-blue-200 text-blue-800 p-4 rounded-lg">
              <p className="font-semibold">Twilio Configuration</p>
              <p className="text-sm mb-2">GSM-7 characters: {smsLength}/160 ({smsSegments} segment{smsSegments > 1 ? 's' : ''})</p>
              <textarea 
                className="w-full border border-gray-300 rounded-lg p-2" 
                rows={4} 
                placeholder="Type your SMS message here..."
                value={smsText}
                onChange={(e) => setSmsText(e.target.value)}
              />
            </div>
          )}

          {channel === 'EMAIL' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Subject Line</label>
              <input type="text" className="w-full border border-gray-300 rounded-lg p-2" />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
