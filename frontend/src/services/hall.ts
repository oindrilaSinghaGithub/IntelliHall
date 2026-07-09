import { apiClient } from "@/services/api-client";

export interface HallPublicRead {
  id: string;
  name: string;
}

// ---------------------------------------------------------------------------
// GET /api/v1/halls/public
// ---------------------------------------------------------------------------

export async function getPublicHalls(): Promise<HallPublicRead[]> {
  const response = await apiClient.get<HallPublicRead[]>("/halls/public");
  return response.data;
}
