import { apiClient } from "@/services/api-client";
import type { HallAnalytics } from "@/types/analytics";

// ---------------------------------------------------------------------------
// GET /api/v1/halls/{hall_id}/analytics
// ---------------------------------------------------------------------------

export async function getHallAnalytics(
  hallId: string,
  months?: number
): Promise<HallAnalytics> {
  const params = months ? { months } : undefined;
  const response = await apiClient.get<HallAnalytics>(
    `/halls/${hallId}/analytics`,
    { params }
  );
  return response.data;
}
