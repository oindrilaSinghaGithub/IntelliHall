import { apiClient } from "@/services/api-client";
import type {
  Worker,
  WorkerCreateRequest,
  WorkerUpdateRequest,
  PaginatedWorkerResponse,
} from "@/types/worker";

// ---------------------------------------------------------------------------
// POST /api/v1/workers/
// ---------------------------------------------------------------------------

export async function createWorker(data: WorkerCreateRequest): Promise<Worker> {
  const response = await apiClient.post<Worker>("/workers/", data);
  return response.data;
}

// ---------------------------------------------------------------------------
// GET /api/v1/workers/
// ---------------------------------------------------------------------------

export async function listWorkers(params?: {
  page?: number;
  page_size?: number;
}): Promise<PaginatedWorkerResponse> {
  const response = await apiClient.get<PaginatedWorkerResponse>("/workers/", {
    params,
  });
  return response.data;
}

// ---------------------------------------------------------------------------
// PUT /api/v1/workers/{id}
// ---------------------------------------------------------------------------

export async function updateWorker(
  id: string,
  data: WorkerUpdateRequest,
): Promise<Worker> {
  const response = await apiClient.put<Worker>(`/workers/${id}`, data);
  return response.data;
}

// ---------------------------------------------------------------------------
// DELETE /api/v1/workers/{id}
// ---------------------------------------------------------------------------

export async function deleteWorker(id: string): Promise<void> {
  await apiClient.delete(`/workers/${id}`);
}
