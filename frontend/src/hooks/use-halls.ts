import { useQuery } from "@tanstack/react-query";

import { getPublicHalls } from "@/services/hall";

export const HALL_KEYS = {
  all: ["halls"] as const,
  public: () => [...HALL_KEYS.all, "public"] as const,
};

// ---------------------------------------------------------------------------
// Hook: get public halls list (cached for 24 hours)
// ---------------------------------------------------------------------------

export function useHalls() {
  return useQuery({
    queryKey: HALL_KEYS.public(),
    queryFn: getPublicHalls,
    staleTime: 24 * 60 * 60 * 1000, // 24 hours
  });
}
