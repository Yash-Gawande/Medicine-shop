export type UserType = "customer" | "staff";

export interface AuthUser {
  id: string;
  email: string;
  mobile: string | null;
  user_type: UserType;
  status: "pending_verification" | "active" | "inactive" | "locked";
  is_email_verified: boolean;
  is_mobile_verified: boolean;
  roles: string[];
  permissions: string[];
}

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  user: AuthUser;
}
