import { apiClient } from "@/services/api-client";
import type {
  Complaint,
  ComplaintCreateRequest,
  ComplaintImage,
  ComplaintSummary,
  CompletionSlip,
  PaginatedResponse,
  RescheduleRequest,
  StatusUpdateRequest,
} from "@/types/complaint";

// ---------------------------------------------------------------------------
// POST /api/v1/complaints/
// ---------------------------------------------------------------------------

export async function createComplaint(data: ComplaintCreateRequest): Promise<Complaint> {
  const response = await apiClient.post<Complaint>("/complaints/", data);
  return response.data;
}

// ---------------------------------------------------------------------------
// POST /api/v1/complaints/{complaint_id}/images
// ---------------------------------------------------------------------------

export async function uploadComplaintImages(
  complaintId: string,
  files: File[],
): Promise<ComplaintImage[]> {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }
  const response = await apiClient.post<{ images: ComplaintImage[] }>(
    `/complaints/${complaintId}/images`,
    formData,
  );
  return response.data.images;
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
// Accepts extended payload with assignment + completion fields.
// ---------------------------------------------------------------------------

export async function updateComplaintStatus(
  id: string,
  data: StatusUpdateRequest
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

// ---------------------------------------------------------------------------
// GET /api/v1/complaints/{complaint_id}/completion-slip
// ---------------------------------------------------------------------------

export async function getCompletionSlip(id: string): Promise<CompletionSlip> {
  const response = await apiClient.get<CompletionSlip>(`/complaints/${id}/completion-slip`);
  return response.data;
}

// ---------------------------------------------------------------------------
// POST /api/v1/complaints/{complaint_id}/confirm
// ---------------------------------------------------------------------------

export async function confirmRepair(id: string, comment?: string | null): Promise<Complaint> {
  const response = await apiClient.post<Complaint>(`/complaints/${id}/confirm`, {
    comment: comment || null,
  });
  return response.data;
}

// ---------------------------------------------------------------------------
// POST /api/v1/complaints/{complaint_id}/reject
// ---------------------------------------------------------------------------

export async function rejectRepair(id: string, comment: string): Promise<Complaint> {
  const response = await apiClient.post<Complaint>(`/complaints/${id}/reject`, { comment });
  return response.data;
}

// ---------------------------------------------------------------------------
// POST /api/v1/complaints/{complaint_id}/reschedule
// ---------------------------------------------------------------------------

export async function rescheduleComplaint(
  id: string,
  data: RescheduleRequest,
): Promise<Complaint> {
  const response = await apiClient.post<Complaint>(`/complaints/${id}/reschedule`, data);
  return response.data;
}

// ---------------------------------------------------------------------------
// POST & DELETE /api/v1/complaints/{complaint_id}/affected
// ---------------------------------------------------------------------------

export async function markAffected(id: string): Promise<{ affected_count: number; is_affected: boolean }> {
  const response = await apiClient.post<{ affected_count: number; is_affected: boolean }>(`/complaints/${id}/affected`);
  return response.data;
}

export async function removeAffected(id: string): Promise<{ affected_count: number; is_affected: boolean }> {
  const response = await apiClient.delete<{ affected_count: number; is_affected: boolean }>(`/complaints/${id}/affected`);
  return response.data;
}

