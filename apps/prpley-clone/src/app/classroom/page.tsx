import React from 'react';
import { Mic, MicOff, Video, VideoOff, MonitorUp, PhoneOff, MessageSquare, Settings } from 'lucide-react';

export default function ClassroomPage() {
  return (
    <div className="bg-gray-900 min-h-screen text-white flex flex-col">
      
      {/* Classroom Header */}
      <header className="bg-gray-900 border-b border-gray-800 p-4 flex justify-between items-center z-10">
        <div className="flex items-center gap-4">
          <div className="bg-red-500 w-2 h-2 rounded-full animate-pulse"></div>
          <span className="font-bold text-gray-300">00:45:12</span>
          <div className="h-4 w-px bg-gray-700"></div>
          <span className="font-bold">English Conversation with Sarah Jenkins</span>
        </div>
        <div className="flex gap-4">
           <button className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition">
             <Settings className="w-5 h-5 text-gray-300" />
           </button>
        </div>
      </header>

      {/* Main Video Area */}
      <main className="flex-1 flex overflow-hidden">
        
        {/* Videos Container */}
        <div className="flex-1 p-4 flex flex-col gap-4">
           {/* Remote Video (Tutor) */}
           <div className="flex-1 bg-black rounded-2xl overflow-hidden relative border border-gray-800">
             <img src="https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=1200&q=80" alt="Tutor camera" className="absolute inset-0 w-full h-full object-cover" />
             <div className="absolute bottom-4 left-4 bg-black/50 backdrop-blur-md px-3 py-1 rounded-lg text-sm font-medium">
               Sarah Jenkins (Tutor)
             </div>
           </div>
           
           {/* Local Video (Student) */}
           <div className="w-64 aspect-video bg-gray-800 rounded-xl overflow-hidden absolute bottom-24 right-8 border-2 border-gray-700 shadow-2xl">
             <div className="w-full h-full flex items-center justify-center text-gray-500">
               Camera Off
             </div>
             <div className="absolute bottom-2 left-2 bg-black/50 backdrop-blur-md px-2 py-0.5 rounded text-xs font-medium">
               You
             </div>
           </div>
        </div>
        
        {/* Chat Sidebar */}
        <div className="w-80 bg-gray-900 border-l border-gray-800 flex flex-col">
          <div className="p-4 border-b border-gray-800 flex items-center gap-2">
            <MessageSquare className="w-5 h-5" />
            <h2 className="font-bold">Chat</h2>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
             <div className="bg-gray-800 p-3 rounded-lg rounded-tl-none self-start max-w-[85%] text-sm">
               Hello! Are you ready for our lesson today?
             </div>
             <div className="bg-teal-600 p-3 rounded-lg rounded-tr-none self-end max-w-[85%] text-sm ml-auto">
               Yes, I'm ready! I struggled a bit with the homework though.
             </div>
             <div className="bg-gray-800 p-3 rounded-lg rounded-tl-none self-start max-w-[85%] text-sm">
               No worries, we can go over it together. Let's start with exercise 2.
             </div>
          </div>
          <div className="p-4 border-t border-gray-800">
             <div className="bg-gray-800 rounded-lg flex items-center px-3 py-2 border border-gray-700">
               <input type="text" placeholder="Type a message..." className="bg-transparent flex-1 outline-none text-sm" />
             </div>
          </div>
        </div>

      </main>

      {/* Controls Bar */}
      <footer className="bg-gray-900 border-t border-gray-800 p-4 flex justify-center items-center gap-4 z-10">
        <button className="p-4 rounded-full bg-gray-800 hover:bg-gray-700 text-white transition">
          <Mic className="w-6 h-6" />
        </button>
        <button className="p-4 rounded-full bg-gray-800 hover:bg-gray-700 text-white transition">
          <VideoOff className="w-6 h-6 text-red-400" />
        </button>
        <button className="p-4 rounded-full bg-gray-800 hover:bg-gray-700 text-white transition">
          <MonitorUp className="w-6 h-6" />
        </button>
        <button className="p-4 rounded-full bg-red-600 hover:bg-red-700 text-white transition ml-4">
          <PhoneOff className="w-6 h-6" />
        </button>
      </footer>

    </div>
  );
}
