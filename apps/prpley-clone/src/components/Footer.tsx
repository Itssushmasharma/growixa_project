import React from 'react';

export default function Footer() {
  return (
    <footer className="bg-gray-900 text-white py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          <div>
            <h3 className="font-bold text-lg mb-4">About us</h3>
            <ul className="space-y-2 text-sm text-gray-400">
              <li>Who we are</li>
              <li>How it works</li>
              <li>Preply reviews</li>
              <li>Work at Preply!</li>
            </ul>
          </div>
          <div>
            <h3 className="font-bold text-lg mb-4">For students</h3>
            <ul className="space-y-2 text-sm text-gray-400">
              <li>Preply Blog</li>
              <li>Preply questions</li>
              <li>Student discount</li>
            </ul>
          </div>
          <div>
            <h3 className="font-bold text-lg mb-4">For tutors</h3>
            <ul className="space-y-2 text-sm text-gray-400">
              <li>Become an online tutor</li>
              <li>Teach English online</li>
              <li>Teach Spanish online</li>
            </ul>
          </div>
          <div>
            <h3 className="font-bold text-lg mb-4">Support</h3>
            <ul className="space-y-2 text-sm text-gray-400">
              <li>Need any help?</li>
            </ul>
          </div>
        </div>
        <div className="border-t border-gray-800 mt-12 pt-8 flex flex-col md:flex-row justify-between items-center text-sm text-gray-500">
          <p>© 2026 Preply Clone Inc.</p>
          <div className="flex space-x-4 mt-4 md:mt-0">
            <span>Privacy Policy</span>
            <span>Cookie Policy</span>
            <span>Terms of Service</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
