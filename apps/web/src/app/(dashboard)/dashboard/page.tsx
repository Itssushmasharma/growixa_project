import { DashboardPage } from "./dashboard-page";

export default function DashboardIndexPage() {
  return (
    <div className="relative">
      {/* Decorative Background */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-100 via-transparent to-transparent opacity-50 pointer-events-none" />
      
      <DashboardPage />
      
      {/* Premium Empty State Overlay (conditionally shown in production if no data) */}
      <div className="mt-8 bg-white border border-gray-200 shadow-xl shadow-indigo-100/20 rounded-2xl p-8 transition-all hover:shadow-2xl hover:shadow-indigo-200/40">
        <div className="flex items-start gap-6">
          <div className="w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-lg">
            <span className="text-3xl">🚀</span>
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900 tracking-tight">Ready to scale your agency?</h2>
            <p className="text-gray-500 mt-2 max-w-2xl leading-relaxed">
              Your dashboard is looking a little empty. Connect your first social account or invite your team members to start populating your analytics and unified inbox.
            </p>
            <div className="mt-6 flex gap-4">
              <button className="bg-gray-900 hover:bg-gray-800 text-white px-6 py-2.5 rounded-xl font-medium shadow-sm transition-all hover:scale-[1.02]">
                Connect Social Account
              </button>
              <button className="bg-indigo-50 text-indigo-700 hover:bg-indigo-100 px-6 py-2.5 rounded-xl font-medium transition-colors">
                Invite Team
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
