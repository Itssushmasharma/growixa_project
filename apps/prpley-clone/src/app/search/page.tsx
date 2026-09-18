import React from 'react';
import TutorCard from '@/components/TutorCard';
import { prisma } from '@/lib/prisma';

export const dynamic = 'force-dynamic';

export default async function SearchPage({
  searchParams,
}: {
  searchParams: { subject?: string; country?: string; minPrice?: string; maxPrice?: string }
}) {
  
  // Build query from URL params
  const query: any = {};
  if (searchParams.subject && searchParams.subject !== 'I want to learn...') {
    query.subject = { contains: searchParams.subject };
  }
  if (searchParams.country && searchParams.country !== 'Tutor is from...') {
    query.country = searchParams.country;
  }
  if (searchParams.minPrice || searchParams.maxPrice) {
    query.price = {};
    if (searchParams.minPrice) query.price.gte = parseFloat(searchParams.minPrice);
    if (searchParams.maxPrice) query.price.lte = parseFloat(searchParams.maxPrice);
  }

  // Fetch from DB using Prisma
  const tutors = await prisma.tutorProfile.findMany({
    where: query,
    include: {
      user: {
        select: { name: true }
      }
    }
  });

  // Fallback to mock data ONLY if DB is completely empty (for prototype demo purposes)
  const displayTutors = tutors.length > 0 ? tutors.map(t => ({
    id: t.userId,
    name: t.user.name,
    subject: t.subject,
    price: t.price,
    rating: t.rating,
    reviews: t.reviewCount,
    country: t.country,
    bio: t.bio,
    imageUrl: t.imageUrl || "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=400&q=80"
  })) : [
    {
      id: "1",
      name: "Sarah Jenkins (Mock)",
      subject: "English",
      price: 25,
      rating: 4.9,
      reviews: 142,
      country: "UK",
      bio: "Certified TEFL teacher with 5+ years of experience. I specialize in conversational English...",
      imageUrl: "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=400&q=80"
    }
  ];

  return (
    <div className="bg-gray-50 min-h-screen pb-12">
      
      {/* Top Filter Bar (Client side filtering would require a client component wrapper, 
          but for now it's static HTML as per standard Next 14 server components without interactivity) */}
      <div className="bg-white border-b border-gray-200 py-4 sticky top-16 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex gap-4 overflow-x-auto">
          <select className="bg-gray-50 border border-gray-300 text-gray-700 text-sm rounded-lg focus:ring-teal-500 focus:border-teal-500 block p-2.5">
            <option>I want to learn...</option>
            <option>English</option>
            <option>Spanish</option>
            <option>French</option>
          </select>
          
          <select className="bg-gray-50 border border-gray-300 text-gray-700 text-sm rounded-lg focus:ring-teal-500 focus:border-teal-500 block p-2.5">
            <option>Price per lesson</option>
            <option>$5 - $15</option>
            <option>$15 - $25</option>
            <option>$25+</option>
          </select>
          
          <select className="bg-gray-50 border border-gray-300 text-gray-700 text-sm rounded-lg focus:ring-teal-500 focus:border-teal-500 block p-2.5">
            <option>Tutor is from...</option>
            <option>United Kingdom</option>
            <option>United States</option>
            <option>Spain</option>
          </select>
        </div>
      </div>
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8 flex gap-8">
        
        {/* Main Content */}
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">
            {displayTutors.length} online tutors available
          </h1>
          
          <div className="space-y-4">
            {displayTutors.map(tutor => (
              <TutorCard key={tutor.id} tutor={tutor as any} />
            ))}
          </div>
          
          <div className="mt-8 flex justify-center">
            <button className="bg-white border border-gray-300 text-gray-700 font-bold py-3 px-8 rounded-xl hover:bg-gray-50 transition">
              Show more tutors
            </button>
          </div>
        </div>
        
        {/* Right Sidebar */}
        <div className="hidden lg:block w-80">
           <div className="bg-teal-50 rounded-2xl p-6 border border-teal-100 sticky top-40">
             <h3 className="font-bold text-lg text-teal-900 mb-2">Not sure where to start?</h3>
             <p className="text-sm text-teal-800 mb-4">
               Take a short quiz to get personalized tutor recommendations based on your goals.
             </p>
             <button className="w-full bg-teal-600 text-white font-bold py-3 px-4 rounded-xl text-sm hover:bg-teal-700 transition">
               Take the quiz
             </button>
           </div>
        </div>
        
      </div>
    </div>
  );
}
