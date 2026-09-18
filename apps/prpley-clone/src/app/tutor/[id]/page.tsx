import React from 'react';
import { Star, Shield, Clock, Video, MessageSquare, Globe, ChevronRight, Play, Calendar as CalendarIcon, CheckCircle2 } from 'lucide-react';
import Link from 'next/link';

export default function TutorProfilePage({ params }: { params: { id: string } }) {
  // Mock Data
  const tutor = {
    id: params.id,
    name: "Sarah Jenkins",
    subject: "English",
    price: 25,
    rating: 4.9,
    reviews: 142,
    country: "UK",
    bio: "Certified TEFL teacher with 5+ years of experience. I specialize in conversational English, business English, and IELTS preparation. My classes are highly interactive and tailored to your specific needs.",
    imageUrl: "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=800&q=80",
    students: 128,
    lessons: 1045
  };

  return (
    <div className="bg-gray-50 min-h-screen pb-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8 flex flex-col lg:flex-row gap-8">
        
        {/* Left Column (Main Info) */}
        <div className="flex-1 space-y-8">
          
          <div className="bg-white rounded-2xl p-8 border border-gray-200">
            <div className="flex flex-col md:flex-row gap-8">
              <div className="shrink-0 relative">
                <img src={tutor.imageUrl} alt={tutor.name} className="w-48 h-48 rounded-2xl object-cover" />
                <div className="absolute -bottom-3 -right-3 bg-white p-2 rounded-full shadow-md">
                   <span className="text-2xl" title={tutor.country}>🇬🇧</span>
                </div>
              </div>
              <div className="flex-1">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">{tutor.name}</h1>
                <p className="text-lg text-gray-700 font-medium mb-4">{tutor.subject} tutor</p>
                
                <div className="flex gap-6 text-sm text-gray-600 mb-6">
                  <div className="flex items-center gap-1">
                    <Star className="w-5 h-5 fill-yellow-400 text-yellow-400" />
                    <span className="font-bold text-gray-900">{tutor.rating}</span>
                    <span>({tutor.reviews} reviews)</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="font-bold text-gray-900">{tutor.students}</span> students
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="font-bold text-gray-900">{tutor.lessons}</span> lessons
                  </div>
                </div>
                
                <h3 className="font-bold text-gray-900 mb-2">About me</h3>
                <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">{tutor.bio}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-2xl p-8 border border-gray-200">
             <h2 className="text-2xl font-bold text-gray-900 mb-6">Schedule</h2>
             {/* Fake Calendar Grid */}
             <div className="border border-gray-200 rounded-xl overflow-hidden">
                <div className="grid grid-cols-7 bg-gray-50 border-b border-gray-200 text-center text-sm font-bold py-3 text-gray-700">
                  <div>Mon</div><div>Tue</div><div>Wed</div><div>Thu</div><div>Fri</div><div>Sat</div><div>Sun</div>
                </div>
                <div className="grid grid-cols-7 h-64 text-center divide-x divide-gray-200">
                  <div className="p-2 space-y-2">
                    <div className="bg-teal-50 text-teal-700 text-xs py-1 rounded cursor-pointer hover:bg-teal-100">09:00</div>
                    <div className="bg-teal-50 text-teal-700 text-xs py-1 rounded cursor-pointer hover:bg-teal-100">10:00</div>
                  </div>
                  <div className="p-2 space-y-2">
                    <div className="bg-teal-50 text-teal-700 text-xs py-1 rounded cursor-pointer hover:bg-teal-100">14:00</div>
                  </div>
                  <div className="p-2"></div>
                  <div className="p-2 space-y-2">
                    <div className="bg-teal-50 text-teal-700 text-xs py-1 rounded cursor-pointer hover:bg-teal-100">11:00</div>
                    <div className="bg-teal-50 text-teal-700 text-xs py-1 rounded cursor-pointer hover:bg-teal-100">15:00</div>
                  </div>
                  <div className="p-2"></div>
                  <div className="p-2"></div>
                  <div className="p-2"></div>
                </div>
             </div>
          </div>

        </div>
        
        {/* Right Sidebar (Booking Widget) */}
        <div className="w-full lg:w-[350px]">
          <div className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm sticky top-24">
             <div className="relative mb-6 rounded-xl overflow-hidden aspect-video bg-gray-900 group cursor-pointer flex items-center justify-center">
                <img src={tutor.imageUrl} alt="Video thumbnail" className="absolute inset-0 w-full h-full object-cover opacity-60 mix-blend-overlay" />
                <div className="w-16 h-16 bg-white/30 backdrop-blur-sm rounded-full flex items-center justify-center group-hover:scale-110 transition z-10">
                  <Play className="w-8 h-8 text-white fill-current ml-1" />
                </div>
             </div>
             
             <div className="flex justify-between items-center mb-6">
               <div className="text-gray-500">50-min lesson</div>
               <div className="text-3xl font-bold text-gray-900">${tutor.price}</div>
             </div>
             
             <Link href="/checkout" className="w-full bg-teal-600 hover:bg-teal-700 text-white font-bold py-4 rounded-xl transition shadow-lg shadow-teal-200 text-lg flex justify-center items-center mb-4">
               Book Trial Lesson
             </Link>
             
             <button className="w-full bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 font-bold py-3 px-4 rounded-xl transition flex items-center justify-center gap-2 mb-6">
               <MessageSquare className="w-5 h-5" />
               Send message
             </button>
             
             <div className="space-y-3 text-sm text-gray-600">
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="w-5 h-5 text-teal-600" />
                  <span>Free replacement if you are not satisfied</span>
                </div>
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="w-5 h-5 text-teal-600" />
                  <span>Verified tutor</span>
                </div>
             </div>
          </div>
        </div>

      </div>
    </div>
  );
}
