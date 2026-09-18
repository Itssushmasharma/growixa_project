import React from 'react';
import { Video, Calendar, MessageSquare, Clock } from 'lucide-react';

export default function StudentDashboard() {
  return (
    <div className="bg-gray-50 min-h-screen">
      
      {/* Dashboard Header */}
      <div className="bg-white border-b border-gray-200 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900">Welcome back, Alex!</h1>
          <p className="text-gray-500 mt-2">You have 1 upcoming lesson this week.</p>
        </div>
      </div>
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8 flex flex-col md:flex-row gap-8">
        
        {/* Main Content Area */}
        <div className="flex-1 space-y-8">
          
          {/* Upcoming Lesson Card */}
          <div className="bg-white rounded-2xl border border-teal-200 shadow-sm overflow-hidden">
             <div className="bg-teal-50 px-6 py-4 border-b border-teal-100 flex justify-between items-center">
               <h3 className="font-bold text-teal-900 flex items-center gap-2">
                 <Calendar className="w-5 h-5 text-teal-600" />
                 Next Lesson
               </h3>
               <span className="text-sm font-bold text-teal-700 bg-teal-100 px-3 py-1 rounded-full">In 2 hours</span>
             </div>
             
             <div className="p-6 flex flex-col sm:flex-row gap-6 items-center sm:items-start justify-between">
                <div className="flex gap-4 items-center">
                  <img src="https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=200&q=80" alt="Tutor" className="w-16 h-16 rounded-full object-cover" />
                  <div>
                    <h4 className="text-xl font-bold text-gray-900">Sarah Jenkins</h4>
                    <p className="text-gray-500">English • Conversational Practice</p>
                    <div className="flex items-center gap-2 text-sm text-gray-600 mt-1 font-medium">
                      <Clock className="w-4 h-4" />
                      <span>Today, 14:00 - 14:50</span>
                    </div>
                  </div>
                </div>
                
                <div className="flex flex-col gap-2 w-full sm:w-auto">
                   <button className="bg-teal-600 hover:bg-teal-700 text-white font-bold py-3 px-6 rounded-xl flex items-center justify-center gap-2 transition shadow-sm">
                     <Video className="w-5 h-5" />
                     Join classroom
                   </button>
                   <button className="bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 font-bold py-2 px-6 rounded-xl flex items-center justify-center gap-2 transition">
                     <MessageSquare className="w-4 h-4" />
                     Message
                   </button>
                </div>
             </div>
          </div>
          
          {/* Past Lessons */}
          <div className="bg-white rounded-2xl border border-gray-200 p-6">
            <h3 className="font-bold text-xl text-gray-900 mb-6">Past Lessons</h3>
            
            <div className="divide-y divide-gray-100">
               <div className="py-4 flex justify-between items-center">
                 <div className="flex gap-4 items-center">
                    <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center text-gray-500 font-bold">SJ</div>
                    <div>
                      <h4 className="font-bold text-gray-900">Sarah Jenkins</h4>
                      <p className="text-sm text-gray-500">Oct 12 • 50 mins</p>
                    </div>
                 </div>
                 <button className="text-teal-600 text-sm font-bold hover:underline">Leave review</button>
               </div>
               
               <div className="py-4 flex justify-between items-center">
                 <div className="flex gap-4 items-center">
                    <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center text-gray-500 font-bold">CM</div>
                    <div>
                      <h4 className="font-bold text-gray-900">Carlos Mendoza</h4>
                      <p className="text-sm text-gray-500">Sep 28 • 50 mins</p>
                    </div>
                 </div>
                 <button className="text-teal-600 text-sm font-bold hover:underline">Book again</button>
               </div>
            </div>
          </div>

        </div>
        
        {/* Right Sidebar (Wallet/Stats) */}
        <div className="w-full md:w-80 space-y-6">
          <div className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm">
             <h3 className="font-bold text-lg text-gray-900 mb-4">My Wallet</h3>
             <div className="text-3xl font-bold text-gray-900 mb-1">$45.00</div>
             <p className="text-sm text-gray-500 mb-6">Available balance</p>
             <button className="w-full bg-white border border-teal-600 text-teal-600 font-bold py-2 px-4 rounded-xl hover:bg-teal-50 transition">
               Add funds
             </button>
          </div>
        </div>

      </div>
    </div>
  );
}
