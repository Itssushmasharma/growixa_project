import { apiFetch } from "../api-client";

export interface AgencyOut {
  id: string;
  name: string;
  subdomain?: string | null;
  custom_domain?: string | null;
  portal_name?: string | null;
  portal_logo_url?: string | null;
  brand_color_primary?: string | null;
  brand_color_secondary?: string | null;
  owner_user_id: string;
  created_at: string;
  updated_at: string;
}

export interface AgencyCreateIn {
  name: string;
  subdomain?: string | null;
  custom_domain?: string | null;
}

export interface ClientOut {
  id: string;
  company_name: string;
  industry?: string | null;
  website_url?: string | null;
  created_at: string;
}

export interface AgencyUpdateIn {
  name?: string;
  subdomain?: string | null;
  custom_domain?: string | null;
  portal_name?: string | null;
  portal_logo_url?: string | null;
  brand_color_primary?: string | null;
  brand_color_secondary?: string | null;
}

export async function fetchAgencies(): Promise<AgencyOut[]> {
  return await apiFetch<AgencyOut[]>("/agencies");
}

export async function createAgency(data: AgencyCreateIn): Promise<AgencyOut> {
  return await apiFetch<AgencyOut>("/agencies", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getAgency(agencyId: string): Promise<AgencyOut> {
  return await apiFetch<AgencyOut>(`/agencies/${agencyId}`);
}

export async function updateAgencyWhiteLabel(
  agencyId: string,
  data: AgencyUpdateIn
): Promise<AgencyOut> {
  return await apiFetch<AgencyOut>(`/agencies/${agencyId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function fetchAgencyClients(agencyId: string): Promise<ClientOut[]> {
  return await apiFetch<ClientOut[]>(`/agencies/${agencyId}/clients`);
}
