import React from 'react';
import { CreditCard, CheckCircle2, Lock, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function CheckoutPage() {
  return (
    <div className="bg-gray-50 min-h-screen py-12">
      <div className="max-w-4xl mx-auto px-4">
        
        <Link href="/search" className="inline-flex items-center text-teal-600 font-medium mb-6 hover:underline">
          <ArrowLeft className="w-4 h-4 mr-2" /> Back to Search
        </Link>
        
        <div className="flex flex-col md:flex-row gap-8">
          {/* Checkout Form (Stripe Mock) */}
          <div className="flex-1 bg-white p-8 rounded-2xl shadow-sm border border-gray-200">
            <div className="flex items-center justify-between mb-8">
              <h1 className="text-2xl font-bold text-gray-900">Checkout</h1>
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <Lock className="w-4 h-4" /> Secure payment
              </div>
            </div>
            
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Card Information</label>
                <div className="border border-gray-300 rounded-xl p-4 bg-gray-50 flex items-center justify-center h-12">
                  {/* Mock Stripe Element */}
                  <span className="text-gray-400 font-mono text-sm tracking-widest flex items-center gap-2">
                    <CreditCard className="w-4 h-4" /> **** **** **** 4242
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Expiry Date</label>
                  <input type="text" placeholder="MM/YY" className="w-full border border-gray-300 rounded-xl p-3 bg-gray-50 text-sm" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">CVC</label>
                  <input type="text" placeholder="123" className="w-full border border-gray-300 rounded-xl p-3 bg-gray-50 text-sm" />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Cardholder Name</label>
                <input type="text" placeholder="John Doe" className="w-full border border-gray-300 rounded-xl p-3 bg-gray-50 text-sm" />
              </div>

              <div className="pt-4 border-t border-gray-100 mt-6">
                <button className="w-full bg-teal-600 hover:bg-teal-700 text-white font-bold py-4 rounded-xl transition shadow-lg shadow-teal-200 text-lg">
                  Pay $25.00
                </button>
              </div>
            </div>
          </div>

          {/* Order Summary */}
          <div className="w-full md:w-96">
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-200">
              <h2 className="text-xl font-bold text-gray-900 mb-6">Order Summary</h2>
              
              <div className="flex gap-4 mb-6">
                <img src="https://images.unsplash.com/photo-1544717305-2782549b5136?w=100&q=80" alt="Tutor" className="w-16 h-16 rounded-xl object-cover" />
                <div>
                  <h3 className="font-bold text-gray-900">Dr. Sarah M.</h3>
                  <p className="text-sm text-gray-500">English Literature</p>
                </div>
              </div>
              
              <div className="space-y-4 text-sm text-gray-600 mb-6 border-y border-gray-100 py-4">
                <div className="flex justify-between">
                  <span>Date & Time</span>
                  <span className="font-medium text-gray-900">Tomorrow, 14:00 - 15:00</span>
                </div>
                <div className="flex justify-between">
                  <span>Duration</span>
                  <span className="font-medium text-gray-900">60 mins</span>
                </div>
              </div>
              
              <div className="space-y-3 mb-6">
                <div className="flex justify-between text-gray-600">
                  <span>Lesson fee</span>
                  <span>$23.00</span>
                </div>
                <div className="flex justify-between text-gray-600">
                  <span>Platform fee</span>
                  <span>$2.00</span>
                </div>
                <div className="flex justify-between font-bold text-lg text-gray-900 pt-3 border-t border-gray-100">
                  <span>Total</span>
                  <span>$25.00</span>
                </div>
              </div>
              
              <div className="flex items-start gap-2 text-xs text-gray-500 bg-gray-50 p-3 rounded-lg border border-gray-100">
                <CheckCircle2 className="w-4 h-4 text-teal-600 shrink-0 mt-0.5" />
                <p>100% satisfaction guarantee. Cancel up to 24 hours before for a full refund.</p>
              </div>
            </div>
          </div>
        </div>
        
      </div>
    </div>
  );
}
