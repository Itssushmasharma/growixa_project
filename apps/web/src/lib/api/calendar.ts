import { apiFetch } from "../api-client";

export interface CalendarEvent {
  id: string;
  channel: "EMAIL" | "SOCIAL" | "WHATSAPP" | "SMS";
  title: string;
  status: string;
  scheduled_at: string | null;
  assignee_id?: string | null;
}

export async function fetchCalendarEvents(): Promise<CalendarEvent[]> {
  return await apiFetch<CalendarEvent[]>("/calendar/events");
}
