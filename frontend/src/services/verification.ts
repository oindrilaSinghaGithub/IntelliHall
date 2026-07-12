import { apiClient } from "@/services/api-client";
import type {
  PaginatedVerificationResponse,
  UpdateHallRequest,
  User,
  VerificationRequestRead,
} from "@/types/auth";

// ---------------------------------------------------------------------------
// GET /api/v1/verification/pending
// ---------------------------------------------------------------------------

export async function getPendingVerifications(
  params?: { page?: number; page_size?: number }
): Promise<PaginatedVerificationResponse> {
  const response = await apiClient.get<PaginatedVerificationResponse>(
    "/verification/pending",
    { params }
  );
  return response.data;
}

// ---------------------------------------------------------------------------
// POST /api/v1/verification/{user_id}/approve
// ---------------------------------------------------------------------------

export async function approveVerification(userId: string): Promise<VerificationRequestRead> {
  const response = await apiClient.post<VerificationRequestRead>(
    `/verification/${userId}/approve`
  );
  return response.data;
}

// ---------------------------------------------------------------------------
// POST /api/v1/verification/{user_id}/reject
// ---------------------------------------------------------------------------

export async function rejectVerification(
  userId: string,
  rejectionReason?: string | null
): Promise<VerificationRequestRead> {
  const response = await apiClient.post<VerificationRequestRead>(
    `/verification/${userId}/reject`,
    { rejection_reason: rejectionReason ?? null }
  );
  return response.data;
}

// ---------------------------------------------------------------------------
// PATCH /api/v1/users/me/hall  (student self-service)
// ---------------------------------------------------------------------------

export async function updateMyHall(data: UpdateHallRequest): Promise<User> {
  const response = await apiClient.patch<User>("/users/me/hall", data);
  return response.data;
}
