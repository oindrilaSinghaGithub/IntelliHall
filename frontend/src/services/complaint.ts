import { apiClient } from "@/services/api-client";
import type {
  Complaint,
  ComplaintCreateRequest,
  ComplaintSummary,
  PaginatedResponse,
} from "@/types/complaint";

// ---------------------------------------------------------------------------
// POST /api/v1/complaints/
// ---------------------------------------------------------------------------

export async function createComplaint(data: ComplaintCreateRequest): Promise<Complaint> {
  const response = await apiClient.post<Complaint>("/complaints/", data);
  return response.data;
}

// ---------------------------------------------------------------------------
// GET /api/v1/complaints/
// ---------------------------------------------------------------------------

export async function getMyComplaints(
  params?: Record<string, string | number | boolean | null | undefined>
): Promise<PaginatedResponse<ComplaintSummary>> {
  const response = await apiClient.get<PaginatedResponse<ComplaintSummary>>("/complaints/", {
    params,
  });
  return response.data;
}

// ---------------------------------------------------------------------------
// GET /api/v1/complaints/{complaint_id}
// ---------------------------------------------------------------------------

export async function getComplaint(id: string): Promise<Complaint> {
  const response = await apiClient.get<Complaint>(`/complaints/${id}`);
  return response.data;
}

// ---------------------------------------------------------------------------
// GET /api/v1/halls/{hall_id}/complaints (Admin list view)
// ---------------------------------------------------------------------------

export async function getHallComplaints(
  hallId: string,
  params?: Record<string, string | number | boolean | null | undefined>
): Promise<PaginatedResponse<ComplaintSummary>> {
  const response = await apiClient.get<PaginatedResponse<ComplaintSummary>>(
    `/halls/${hallId}/complaints`,
    { params }
  );
  return response.data;
}

// ---------------------------------------------------------------------------
// PATCH /api/v1/complaints/{complaint_id}/status (Admin transition status)
// ---------------------------------------------------------------------------

export async function updateComplaintStatus(
  id: string,
  data: { new_status: string; remarks?: string | null }
): Promise<Complaint> {
  const response = await apiClient.patch<Complaint>(`/complaints/${id}/status`, data);
  return response.data;
}

// ---------------------------------------------------------------------------
// PATCH /api/v1/complaints/{complaint_id} (Admin update fields)
// ---------------------------------------------------------------------------

export async function updateComplaintFields(
  id: string,
  data: Record<string, unknown>
): Promise<Complaint> {
  const response = await apiClient.patch<Complaint>(`/complaints/${id}`, data);
  return response.data;
}

// ---------------------------------------------------------------------------
// DELETE /api/v1/complaints/{complaint_id} (Admin delete complaint)
// ---------------------------------------------------------------------------

export async function deleteComplaint(id: string): Promise<void> {
  await apiClient.delete(`/complaints/${id}`);
}

