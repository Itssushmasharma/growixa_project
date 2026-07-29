export interface MeResponse {
  id: string;
  email: string;
  full_name: string;
  permissions: string[];
}

export interface Role {
  id: string;
  name: string;
}

export interface TeamMember {
  id: string;
  email: string;
  full_name: string;
  status: "ACTIVE" | "DISABLED";
  last_login_at: string | null;
  roles: string[];
}

export interface InviteResult {
  id: string;
  email: string;
  expires_at: string;
  token: string;
}
