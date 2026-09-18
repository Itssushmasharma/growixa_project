import { UnifiedInbox } from "@/components/inbox/UnifiedInbox";

export default function InboxPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Unified Inbox</h1>
        <p className="mt-2 text-sm text-gray-500">
          Manage all your cross-channel communications (WhatsApp, Social, Email) from one place.
        </p>
      </div>

      <UnifiedInbox />
    </div>
  );
}
