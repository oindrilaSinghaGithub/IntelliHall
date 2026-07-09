// User roles matching the backend enums
export type UserRole = "student" | "hall_admin";

// User model returned by GET /api/v1/auth/me
export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  hall_id: string | null;
  hall_name: string | null;
  created_at: string;
  updated_at: string;
}

// Auth responses
export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface RegisterResponse {
  user: User;
  access_token: string;
  token_type: string;
}

// Auth request bodies
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
  role?: UserRole;
  hall_id?: string | null;
}

// Generic API error shape from FastAPI
export interface ApiError {
  detail: string | { loc: string[]; msg: string; type: string }[];
}
