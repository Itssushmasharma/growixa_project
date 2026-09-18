import React from 'react';
import Link from 'next/link';
import { Mail, Lock, Globe, User, BookOpen, UserCircle } from 'lucide-react';

export default function SignupPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <Link href="/" className="flex items-center justify-center gap-2 mb-6">
          <div className="w-10 h-10 bg-teal-600 rounded-xl flex items-center justify-center">
            <Globe className="w-6 h-6 text-white" />
          </div>
          <span className="text-2xl font-black tracking-tight text-gray-900">LingoMaster</span>
        </Link>
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Create your account
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Already have an account?{' '}
          <Link href="/login" className="font-medium text-teal-600 hover:text-teal-500">
            Sign in
          </Link>
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-2xl sm:px-10 border border-gray-100">
          
          {/* Role Selection */}
          <div className="mb-6 grid grid-cols-2 gap-4">
            <button className="flex flex-col items-center justify-center p-4 border-2 border-teal-600 bg-teal-50 rounded-xl transition">
               <UserCircle className="w-8 h-8 text-teal-600 mb-2" />
               <span className="font-bold text-teal-900">Student</span>
            </button>
            <button className="flex flex-col items-center justify-center p-4 border-2 border-gray-200 hover:border-gray-300 rounded-xl transition">
               <BookOpen className="w-8 h-8 text-gray-500 mb-2" />
               <span className="font-bold text-gray-700">Tutor</span>
            </button>
          </div>
          
          <form className="space-y-6" action="#" method="POST">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                Full Name
              </label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="name"
                  name="name"
                  type="text"
                  required
                  className="focus:ring-teal-500 focus:border-teal-500 block w-full pl-10 sm:text-sm border-gray-300 rounded-xl p-3 bg-gray-50 border"
                  placeholder="John Doe"
                />
              </div>
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email address
              </label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  className="focus:ring-teal-500 focus:border-teal-500 block w-full pl-10 sm:text-sm border-gray-300 rounded-xl p-3 bg-gray-50 border"
                  placeholder="you@example.com"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  className="focus:ring-teal-500 focus:border-teal-500 block w-full pl-10 sm:text-sm border-gray-300 rounded-xl p-3 bg-gray-50 border"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <div>
              <Link href="/dashboard" className="w-full flex justify-center py-3 px-4 border border-transparent rounded-xl shadow-sm text-sm font-bold text-white bg-teal-600 hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500 transition">
                Create Account
              </Link>
            </div>
          </form>
          
          <p className="mt-6 text-center text-xs text-gray-500">
            By signing up, you agree to our Terms of Service and Privacy Policy.
          </p>

        </div>
      </div>
    </div>
  );
}
