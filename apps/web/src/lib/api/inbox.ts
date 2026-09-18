import { apiFetch } from '../api-client';

export type ChannelType = 'WHATSAPP' | 'SOCIAL' | 'EMAIL' | 'SMS';

export interface InboxConversation {
  id: string;
  account_id: string;
  contact_id?: string;
  channel: ChannelType;
  channel_identity?: string;
  status: 'OPEN' | 'RESOLVED' | 'SNOOZED';
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  // Included in API response for convenience if we have contact info
  contact_name?: string;
  contact_email?: string;
}

export interface InboxMessage {
  id: string;
  conversation_id: string;
  direction: 'INBOUND' | 'OUTBOUND';
  content: string;
  media_urls?: string[];
  status: 'RECEIVED' | 'SENT' | 'DELIVERED' | 'READ' | 'FAILED';
  error_message?: string;
  external_id?: string;
  created_at: string;
  updated_at: string;
}

export const inboxApi = {
  getConversations: async (): Promise<InboxConversation[]> => {
    return apiFetch<InboxConversation[]>('/inbox/conversations');
  },

  getMessages: async (conversationId: string): Promise<InboxMessage[]> => {
    return apiFetch<InboxMessage[]>(`/inbox/conversations/${conversationId}/messages`);
  },

  sendMessage: async (conversationId: string, content: string, media_urls?: string[]): Promise<InboxMessage> => {
    return apiFetch<InboxMessage>(`/inbox/conversations/${conversationId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ content, media_urls }),
    });
  },
};
