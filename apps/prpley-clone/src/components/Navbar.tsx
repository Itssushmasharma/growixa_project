import React from 'react';
import { Search, Globe, LogIn } from 'lucide-react';
import Link from 'next/link';

export default function Navbar() {
  return (
    <nav className="border-b border-gray-200 bg-white sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          
          <div className="flex items-center gap-8">
            <Link href="/" className="text-2xl font-bold text-teal-600 tracking-tight">
              preply
            </Link>
            
            <div className="hidden md:flex items-center space-x-6 text-sm font-medium text-gray-700">
              <Link href="/search" className="hover:text-teal-600 transition">Find tutors</Link>
              <Link href="#" className="hover:text-teal-600 transition">Corporate training</Link>
              <Link href="#" className="hover:text-teal-600 transition">Become a tutor</Link>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center gap-1 text-sm text-gray-700 hover:bg-gray-100 p-2 rounded-md cursor-pointer transition">
              <Globe className="w-4 h-4" />
              <span>English, USD</span>
            </div>
            
            <Link href="/login" className="text-gray-700 hover:text-gray-900 font-medium">Log in</Link>
            <Link href="/signup" className="bg-teal-600 text-white px-4 py-2 rounded-xl font-bold hover:bg-teal-700 transition shadow-sm">
              Sign up
            </Link>
          </div>
          
        </div>
      </div>
    </nav>
  );
}
