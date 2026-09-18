import { Metadata } from "next";
import { Inter } from "next/font/google";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Client Portal",
  description: "Client Portal for Campaign and Content Approvals",
};

export default function PortalLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className={`min-h-screen bg-gray-50 ${inter.className}`}>
      {/* 
        Phase A: White-label layout
        Here we will dynamically load agency configuration (logo, colors)
        based on the authenticated user's agency/client context.
      */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Client Portal</h1>
          <nav>
            <span className="text-gray-500">Approvals</span>
          </nav>
        </div>
      </header>
      <main>
        <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          {children}
        </div>
      </main>
    </div>
  );
}
