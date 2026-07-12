import { apiClient } from "@/services/api-client";

export interface ScheduleItem {
  complaint_id: string;
  complaint_title: string;
  room_number: string | null;
  category: string;
  status: string;
  visit_date: string;
  scheduled_time: string | null;
  worker_name: string;
  worker_type: string;
  admin_remarks: string | null;
}

export interface ScheduleFilters {
  scheduled_date?: string | null;
  worker_name?: string | null;
  worker_type?: string | null;
  category?: string | null;
}

// ---------------------------------------------------------------------------
// GET /api/v1/halls/{hall_id}/schedule
// ---------------------------------------------------------------------------

export async function getSchedule(
  hallId: string,
  filters?: ScheduleFilters
): Promise<ScheduleItem[]> {
  const params: Record<string, string> = {};
  if (filters?.scheduled_date) params.scheduled_date = filters.scheduled_date;
  if (filters?.worker_name) params.worker_name = filters.worker_name;
  if (filters?.worker_type) params.worker_type = filters.worker_type;
  if (filters?.category) params.category = filters.category;

  const response = await apiClient.get<ScheduleItem[]>(
    `/halls/${hallId}/schedule/`,
    { params }
  );
  return response.data;
}

// ---------------------------------------------------------------------------
// GET /api/v1/halls/{hall_id}/schedule/export  → returns Blob for download
// ---------------------------------------------------------------------------

export async function exportSchedulePdf(
  hallId: string,
  filters?: ScheduleFilters
): Promise<Blob> {
  const params: Record<string, string> = {};
  if (filters?.scheduled_date) params.scheduled_date = filters.scheduled_date;
  if (filters?.worker_name) params.worker_name = filters.worker_name;
  if (filters?.worker_type) params.worker_type = filters.worker_type;
  if (filters?.category) params.category = filters.category;

  const response = await apiClient.get(`/halls/${hallId}/schedule/export`, {
    params,
    responseType: "blob",
  });
  return response.data as Blob;
}
