import { apiClient } from "@/services/api-client";
import type {
  Complaint,
  ComplaintCreateRequest,
  ComplaintImage,
  ComplaintSummary,
  CompletionSlip,
  PaginatedResponse,
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
// POST /api/v1/complaints/{complaint_id}/images (Upload images)
// ---------------------------------------------------------------------------

export async function uploadComplaintImages(
  complaintId: string,
  files: File[],
  onProgress?: (percent: number) => void,
): Promise<ComplaintImage[]> {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  const response = await apiClient.post<ComplaintImage[]>(
    `/complaints/${complaintId}/images`,
    formData,
    {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (e) => {
        if (onProgress && e.total) {
          onProgress(Math.round((e.loaded * 100) / e.total));
        }
      },
    },
  );
  return response.data;
}

// ---------------------------------------------------------------------------
// DELETE /api/v1/complaints/images/{image_id} (Delete a single image)
// ---------------------------------------------------------------------------

export async function deleteComplaintImage(imageId: string): Promise<void> {
  await apiClient.delete(`/complaints/images/${imageId}`);
}
