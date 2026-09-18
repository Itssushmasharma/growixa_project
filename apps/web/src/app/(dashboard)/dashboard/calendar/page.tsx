import { CalendarView } from "@/components/calendar/CalendarView";

export default function UnifiedCalendarPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Content Calendar</h1>
        <p className="mt-2 text-sm text-gray-500">
          Manage all your scheduled social posts, email campaigns, WhatsApp messages, and SMS campaigns in one place.
        </p>
      </div>

      <CalendarView />
    </div>
  );
}
