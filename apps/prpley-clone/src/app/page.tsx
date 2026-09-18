import React from 'react';
import Link from 'next/link';
import { Search, Globe, LogIn } from 'lucide-react';

export default function Home() {
  return (
    <div className="bg-[#f0f3eb] min-h-screen">
      
      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 flex flex-col md:flex-row items-center justify-between gap-12">
        <div className="md:w-1/2">
          <h1 className="text-5xl font-bold text-gray-900 leading-tight mb-6">
            Unlock your potential with the best online tutors.
          </h1>
          <p className="text-xl text-gray-700 mb-8">
            Learn from native speakers and expert tutors around the world.
          </p>
          
          <div className="bg-white p-4 rounded-xl shadow-lg flex gap-4 max-w-lg">
            <div className="flex-1">
              <label className="text-xs font-bold text-gray-500 uppercase tracking-wide">Language or Subject</label>
              <input type="text" placeholder="e.g. English, Math..." className="w-full mt-1 text-lg outline-none text-gray-900" />
            </div>
            <button className="bg-teal-600 hover:bg-teal-700 text-white p-4 rounded-lg flex items-center justify-center transition">
              <Search className="w-6 h-6" />
            </button>
          </div>
          
          <div className="mt-8 flex items-center gap-4 text-sm font-medium text-gray-600">
            <div className="flex -space-x-2">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="w-8 h-8 rounded-full border-2 border-white bg-gray-300"></div>
              ))}
            </div>
            <p>Over <span className="font-bold text-gray-900">32,000</span> experienced tutors</p>
          </div>
        </div>
        
        <div className="md:w-1/2 flex justify-center">
          <div className="w-full max-w-md aspect-square bg-white rounded-[40px] shadow-2xl p-8 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-teal-100 rounded-bl-full opacity-50"></div>
            <div className="absolute bottom-0 left-0 w-40 h-40 bg-yellow-100 rounded-tr-full opacity-50"></div>
            <div className="relative z-10 flex flex-col items-center justify-center h-full text-center">
               <h3 className="text-2xl font-bold mb-4">Focus on your goals</h3>
               <div className="bg-gray-50 p-4 rounded-xl shadow-sm w-full mb-4 flex items-center gap-4">
                 <div className="w-12 h-12 bg-teal-200 rounded-full flex items-center justify-center font-bold text-teal-800">1</div>
                 <div className="text-left">
                   <div className="font-bold text-gray-900">Find the right tutor</div>
                   <div className="text-xs text-gray-500">Read reviews and watch intros</div>
                 </div>
               </div>
               <div className="bg-gray-50 p-4 rounded-xl shadow-sm w-full mb-4 flex items-center gap-4">
                 <div className="w-12 h-12 bg-teal-200 rounded-full flex items-center justify-center font-bold text-teal-800">2</div>
                 <div className="text-left">
                   <div className="font-bold text-gray-900">Book a lesson</div>
                   <div className="text-xs text-gray-500">Find a time that suits you</div>
                 </div>
               </div>
               <div className="bg-gray-50 p-4 rounded-xl shadow-sm w-full flex items-center gap-4">
                 <div className="w-12 h-12 bg-teal-200 rounded-full flex items-center justify-center font-bold text-teal-800">3</div>
                 <div className="text-left">
                   <div className="font-bold text-gray-900">Start learning</div>
                   <div className="text-xs text-gray-500">In our virtual classroom</div>
                 </div>
               </div>
            </div>
          </div>
        </div>
      </section>

      {/* Popular Subjects */}
      <section className="bg-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-10 text-center">What do you want to learn?</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {['English tutors', 'Spanish tutors', 'French tutors', 'German tutors', 'Math tutors', 'Python tutors', 'Piano tutors', 'Singing tutors'].map((subject) => (
              <Link href="/search" key={subject} className="border border-gray-200 p-6 rounded-xl hover:border-teal-500 hover:shadow-md transition text-center font-medium text-gray-800 cursor-pointer">
                {subject}
              </Link>
            ))}
          </div>
        </div>
      </section>

    </div>
  );
}
