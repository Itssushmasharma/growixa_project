import { apiFetch } from "../api-client";

export interface ApprovalRequestResponse {
  id: string;
  account_id: string;
  entity_type: string;
  entity_id: string;
  requester_id: string;
  reviewer_id: string | null;
  status: string;
  comments: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApprovalRequestListResponse {
  items: ApprovalRequestResponse[];
  total: number;
}

export async function fetchApprovals(status?: string): Promise<ApprovalRequestListResponse> {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  return apiFetch<ApprovalRequestListResponse>(`/approvals${query}`);
}

export async function updateApprovalStatus(id: string, status: string, comments?: string): Promise<ApprovalRequestResponse> {
  return apiFetch<ApprovalRequestResponse>(`/approvals/${id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status, comments }),
  });
}
