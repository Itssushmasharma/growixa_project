import React from 'react';
import { Star, Video, Play, MessageSquare, Calendar } from 'lucide-react';

interface TutorProps {
  id: string;
  name: string;
  subject: string;
  price: number;
  rating: number;
  reviews: number;
  country: string;
  bio: string;
  imageUrl: string;
}

export default function TutorCard({ tutor }: { tutor: TutorProps }) {
  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-6 flex flex-col md:flex-row gap-6 hover:shadow-lg transition">
      
      {/* Left Column: Image & Video */}
      <div className="flex flex-col items-center gap-3 shrink-0">
        <div className="relative">
          <img src={tutor.imageUrl} alt={tutor.name} className="w-32 h-32 rounded-xl object-cover" />
          <div className="absolute -bottom-2 -right-2 bg-white rounded-full p-1 shadow-sm">
            <span className="text-xl" title={tutor.country}>🇬🇧</span>
          </div>
        </div>
        <button className="flex items-center gap-1 text-sm font-bold text-teal-600 bg-teal-50 px-3 py-1.5 rounded-lg hover:bg-teal-100 transition w-full justify-center">
          <Play className="w-4 h-4 fill-current" />
          Video
        </button>
      </div>
      
      {/* Middle Column: Info */}
      <div className="flex-1">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="text-xl font-bold text-gray-900">{tutor.name}</h3>
            <p className="text-sm text-gray-500 font-medium">{tutor.subject} tutor</p>
          </div>
          <div className="flex flex-col items-end">
            <div className="flex items-center gap-1 text-gray-900 font-bold">
              <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
              {tutor.rating}
            </div>
            <p className="text-xs text-gray-500">{tutor.reviews} reviews</p>
          </div>
        </div>
        
        <p className="mt-4 text-gray-700 text-sm line-clamp-3">
          {tutor.bio}
        </p>
        
        <div className="mt-4 flex items-center gap-4 text-sm text-gray-600 font-medium">
          <div className="flex items-center gap-1">
            <MessageSquare className="w-4 h-4" />
            <span>Responds quickly</span>
          </div>
        </div>
      </div>
      
      {/* Right Column: Pricing & Booking */}
      <div className="shrink-0 flex flex-col justify-between items-end md:w-48 border-t md:border-t-0 md:border-l border-gray-100 pt-4 md:pt-0 md:pl-6">
        <div className="text-right">
          <div className="text-2xl font-bold text-gray-900">${tutor.price}</div>
          <div className="text-xs text-gray-500">50-min lesson</div>
        </div>
        
        <div className="flex flex-col gap-2 w-full mt-4">
          <button className="bg-teal-600 hover:bg-teal-700 text-white font-bold py-3 px-4 rounded-xl text-sm transition">
            Book trial lesson
          </button>
          <button className="bg-white border border-gray-300 hover:border-gray-400 text-gray-700 font-bold py-3 px-4 rounded-xl text-sm transition flex items-center justify-center gap-2">
            <MessageSquare className="w-4 h-4" />
            Send message
          </button>
        </div>
      </div>
      
    </div>
  );
}
