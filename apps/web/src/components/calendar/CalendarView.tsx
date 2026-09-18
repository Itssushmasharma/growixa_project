"use client";

import { useState, useEffect } from "react";
import { format, startOfWeek, endOfWeek, eachDayOfInterval, startOfMonth, endOfMonth, isSameDay } from "date-fns";
import { CalendarEvent, fetchCalendarEvents } from "@/lib/api/calendar";

export function CalendarView() {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [currentDate] = useState(new Date());
  const [view, setView] = useState<"month" | "week" | "list">("month");
  const [filterChannel, setFilterChannel] = useState<string>("ALL");

  useEffect(() => {
    fetchCalendarEvents().then(setEvents).catch(console.error);
  }, []);

  const startDay = view === "month" ? startOfMonth(currentDate) : startOfWeek(currentDate);
  const endDay = view === "month" ? endOfMonth(currentDate) : endOfWeek(currentDate);
  const days = eachDayOfInterval({ start: startDay, end: endDay });

  const filteredEvents = events.filter(e => filterChannel === "ALL" || e.channel === filterChannel);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">{format(currentDate, "MMMM yyyy")}</h2>
        <div className="flex gap-4">
          <select 
            value={filterChannel} 
            onChange={(e) => setFilterChannel(e.target.value)}
            className="rounded-md border-gray-300 py-1.5 text-gray-900 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          >
            <option value="ALL">All Channels</option>
            <option value="EMAIL">Email</option>
            <option value="SOCIAL">Social</option>
            <option value="WHATSAPP">WhatsApp</option>
            <option value="SMS">SMS</option>
          </select>
          <div className="flex rounded-md shadow-sm">
            <button onClick={() => setView("month")} className={`px-4 py-2 text-sm font-medium border border-gray-300 rounded-l-md ${view === "month" ? "bg-indigo-50 text-indigo-700" : "bg-white text-gray-700"}`}>Month</button>
            <button onClick={() => setView("week")} className={`px-4 py-2 text-sm font-medium border border-gray-300 ${view === "week" ? "bg-indigo-50 text-indigo-700" : "bg-white text-gray-700"}`}>Week</button>
            <button onClick={() => setView("list")} className={`px-4 py-2 text-sm font-medium border border-gray-300 rounded-r-md ${view === "list" ? "bg-indigo-50 text-indigo-700" : "bg-white text-gray-700"}`}>List</button>
          </div>
        </div>
      </div>

      {view === "list" ? (
        <div className="space-y-4">
          {filteredEvents.map(event => (
            <div key={event.id} className="p-4 border border-gray-200 rounded-lg flex justify-between items-center hover:bg-gray-50">
              <div>
                <span className="inline-flex items-center rounded-md bg-indigo-50 px-2 py-1 text-xs font-medium text-indigo-700 mb-1">{event.channel}</span>
                <h3 className="text-sm font-medium text-gray-900">{event.title}</h3>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-500">{event.scheduled_at ? format(new Date(event.scheduled_at), "MMM d, h:mm a") : "Unscheduled"}</p>
                <span className="text-xs font-medium text-gray-400">{event.status}</span>
              </div>
            </div>
          ))}
          {filteredEvents.length === 0 && <p className="text-center text-gray-500 py-8">No events found.</p>}
        </div>
      ) : (
        <div className={`grid ${view === "month" ? "grid-cols-7" : "grid-cols-7"} gap-px bg-gray-200 rounded-lg overflow-hidden border border-gray-200`}>
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(d => (
            <div key={d} className="bg-gray-50 py-2 text-center text-xs font-semibold text-gray-500">{d}</div>
          ))}
          {days.map(day => (
            <div key={day.toISOString()} className={`bg-white min-h-[100px] p-2 ${isSameDay(day, new Date()) ? "bg-blue-50" : ""}`}>
              <div className="font-medium text-sm text-gray-900 mb-2">{format(day, "d")}</div>
              <div className="space-y-1">
                {filteredEvents.filter(e => e.scheduled_at && isSameDay(new Date(e.scheduled_at), day)).map(event => (
                  <div key={event.id} className="text-xs p-1 rounded bg-indigo-100 text-indigo-800 truncate" title={event.title}>
                    {event.channel.charAt(0)}: {event.title}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
