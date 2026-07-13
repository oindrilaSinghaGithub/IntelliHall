import { useQuery } from "@tanstack/react-query";
import { getHallAnalytics } from "@/services/analytics";

export const ANALYTICS_KEYS = {
  all: ["analytics"] as const,
  hall: (hallId: string, months?: number) =>
    [...ANALYTICS_KEYS.all, "hall", hallId, { months }] as const,
};

export function useHallAnalytics(hallId: string, months?: number) {
  return useQuery({
    queryKey: ANALYTICS_KEYS.hall(hallId, months),
    queryFn: () => getHallAnalytics(hallId, months),
    enabled: !!hallId, // only run when hallId is present
    staleTime: 5 * 60 * 1000, // 5 minutes cache stale time
  });
}
