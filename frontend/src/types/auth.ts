// User roles matching the backend enums
export type UserRole = "student" | "hall_admin";

// Hall verification status matching backend HallVerificationStatus enum
export type HallVerificationStatus = "pending" | "approved" | "rejected";

// User model returned by GET /api/v1/auth/me
export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  hall_id: string | null;
  hall_name: string | null;
  roll_number: string | null;
  room_number: string | null;
  hall_verification_status: HallVerificationStatus;
  verified_by_admin_id: string | null;
  hall_verified_at: string | null;
  hall_rejection_reason: string | null;
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
  roll_number?: string | null;
  room_number?: string | null;
}

// Verification types
export interface VerificationRequestRead {
  id: string;
  name: string;
  email: string;
  roll_number: string | null;
  room_number: string | null;
  hall_id: string | null;
  hall_name: string | null;
  hall_verification_status: HallVerificationStatus;
  hall_rejection_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaginatedVerificationResponse {
  items: VerificationRequestRead[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface UpdateHallRequest {
  hall_id: string;
  room_number?: string | null;
}

// Generic API error shape from FastAPI
export interface ApiError {
  detail: string | { loc: string[]; msg: string; type: string }[];
}

