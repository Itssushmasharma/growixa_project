import React from 'react';
import { Calendar, Clock, DollarSign, Users, Video, MessageSquare, Edit3 } from 'lucide-react';

export default function TutorDashboard() {
  return (
    <div className="bg-gray-50 min-h-screen">
      
      {/* Dashboard Header */}
      <div className="bg-white border-b border-gray-200 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-between items-end">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Tutor Dashboard</h1>
            <p className="text-gray-500 mt-2">Manage your availability, students, and earnings.</p>
          </div>
          <button className="bg-teal-50 text-teal-700 font-bold py-2 px-4 rounded-xl flex items-center gap-2 hover:bg-teal-100 transition">
            <Edit3 className="w-4 h-4" />
            Edit public profile
          </button>
        </div>
      </div>
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8 space-y-8">
        
        {/* Stats Row */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
           <div className="bg-white rounded-2xl p-6 border border-gray-200 flex items-center gap-4">
             <div className="w-12 h-12 bg-teal-100 rounded-full flex items-center justify-center text-teal-600">
               <DollarSign className="w-6 h-6" />
             </div>
             <div>
               <div className="text-sm text-gray-500 font-medium">This month</div>
               <div className="text-2xl font-bold text-gray-900">$1,240</div>
             </div>
           </div>
           
           <div className="bg-white rounded-2xl p-6 border border-gray-200 flex items-center gap-4">
             <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center text-blue-600">
               <Calendar className="w-6 h-6" />
             </div>
             <div>
               <div className="text-sm text-gray-500 font-medium">Upcoming</div>
               <div className="text-2xl font-bold text-gray-900">12 lessons</div>
             </div>
           </div>
           
           <div className="bg-white rounded-2xl p-6 border border-gray-200 flex items-center gap-4">
             <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center text-purple-600">
               <Users className="w-6 h-6" />
             </div>
             <div>
               <div className="text-sm text-gray-500 font-medium">Active students</div>
               <div className="text-2xl font-bold text-gray-900">18</div>
             </div>
           </div>
           
           <div className="bg-white rounded-2xl p-6 border border-gray-200 flex items-center gap-4">
             <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center text-yellow-600">
               <Clock className="w-6 h-6" />
             </div>
             <div>
               <div className="text-sm text-gray-500 font-medium">Hours taught</div>
               <div className="text-2xl font-bold text-gray-900">104</div>
             </div>
           </div>
        </div>

        <div className="flex flex-col lg:flex-row gap-8">
           
           {/* Left Column: Upcoming Classes */}
           <div className="flex-1 space-y-6">
             <h2 className="text-xl font-bold text-gray-900">Today's Schedule</h2>
             
             <div className="space-y-4">
               {/* Next Lesson Highlight */}
               <div className="bg-teal-50 border border-teal-200 rounded-2xl p-6 relative overflow-hidden">
                 <div className="absolute top-0 right-0 w-2 h-full bg-teal-500"></div>
                 <div className="flex justify-between items-start mb-4">
                    <span className="bg-white text-teal-800 font-bold px-3 py-1 rounded-full text-xs shadow-sm">Starts in 45 mins</span>
                 </div>
                 <div className="flex gap-4 items-center mb-6">
                    <img src="https://images.unsplash.com/photo-1517841905240-472988babdf9?w=100&q=80" alt="Student" className="w-16 h-16 rounded-full object-cover border-2 border-white shadow-sm" />
                    <div>
                      <h3 className="text-xl font-bold text-gray-900">Mei Lin (Student)</h3>
                      <div className="flex items-center gap-2 text-gray-600 text-sm mt-1">
                        <Clock className="w-4 h-4" /> 14:00 - 14:50 (50 mins)
                      </div>
                    </div>
                 </div>
                 <div className="flex gap-2">
                   <button className="flex-1 bg-teal-600 hover:bg-teal-700 text-white font-bold py-3 px-4 rounded-xl flex items-center justify-center gap-2 transition">
                     <Video className="w-5 h-5" /> Start Classroom
                   </button>
                   <button className="bg-white hover:bg-gray-50 text-gray-700 border border-gray-300 font-bold py-3 px-4 rounded-xl transition">
                     <MessageSquare className="w-5 h-5" />
                   </button>
                 </div>
               </div>

               {/* Later Lesson */}
               <div className="bg-white border border-gray-200 rounded-2xl p-6 flex items-center justify-between hover:shadow-md transition">
                 <div className="flex items-center gap-4">
                    <div className="text-right border-r border-gray-200 pr-4">
                      <div className="font-bold text-gray-900">16:00</div>
                      <div className="text-xs text-gray-500">50 mins</div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center font-bold text-gray-600">JD</div>
                      <div>
                        <div className="font-bold text-gray-900">John Doe</div>
                        <div className="text-sm text-gray-500">Conversational English</div>
                      </div>
                    </div>
                 </div>
                 <button className="text-teal-600 font-bold text-sm bg-teal-50 px-4 py-2 rounded-lg hover:bg-teal-100 transition">
                   Details
                 </button>
               </div>
             </div>
           </div>

           {/* Right Column: Availability & Settings */}
           <div className="w-full lg:w-96 space-y-6">
              
              {/* Availability Manager */}
              <div className="bg-white border border-gray-200 rounded-2xl p-6">
                <div className="flex justify-between items-center mb-6">
                  <h3 className="font-bold text-lg text-gray-900">My Availability</h3>
                  <button className="text-teal-600 text-sm font-bold hover:underline">Edit</button>
                </div>
                
                <div className="space-y-3">
                  <div className="flex justify-between items-center py-2 border-b border-gray-100">
                    <span className="text-gray-600 font-medium">Mon - Fri</span>
                    <span className="text-gray-900 font-bold">09:00 - 17:00</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-gray-100">
                    <span className="text-gray-600 font-medium">Saturday</span>
                    <span className="text-gray-900 font-bold">10:00 - 14:00</span>
                  </div>
                  <div className="flex justify-between items-center py-2">
                    <span className="text-gray-600 font-medium">Sunday</span>
                    <span className="text-red-500 font-bold">Off</span>
                  </div>
                </div>
              </div>
              
              {/* Profile Completeness */}
              <div className="bg-white border border-gray-200 rounded-2xl p-6">
                <h3 className="font-bold text-lg text-gray-900 mb-2">Profile Score</h3>
                <div className="w-full bg-gray-200 rounded-full h-2.5 mb-4">
                  <div className="bg-teal-600 h-2.5 rounded-full" style={{ width: '85%' }}></div>
                </div>
                <ul className="text-sm space-y-2 text-gray-600">
                  <li className="flex items-center gap-2 text-teal-600 font-medium">✓ Video uploaded</li>
                  <li className="flex items-center gap-2 text-teal-600 font-medium">✓ Description added</li>
                  <li className="flex items-center gap-2">○ Upload certificate</li>
                </ul>
              </div>

           </div>

        </div>

      </div>
    </div>
  );
}
