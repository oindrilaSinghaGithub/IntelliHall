import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";

import {
  exportSchedulePdf,
  getSchedule,
  type ScheduleFilters,
} from "@/services/schedule";
import { extractApiError } from "@/services/api-client";

export const SCHEDULE_KEYS = {
  all: ["schedule"] as const,
  hall: (hallId: string, filters?: ScheduleFilters) =>
    [...SCHEDULE_KEYS.all, hallId, filters || {}] as const,
};

// ---------------------------------------------------------------------------
// Hook: get schedule for a hall
// ---------------------------------------------------------------------------

export function useSchedule(hallId: string, filters?: ScheduleFilters) {
  return useQuery({
    queryKey: SCHEDULE_KEYS.hall(hallId, filters),
    queryFn: () => getSchedule(hallId, filters),
    enabled: !!hallId,
    staleTime: 30000,
  });
}

// ---------------------------------------------------------------------------
// Hook: export schedule as PDF (triggers download)
// ---------------------------------------------------------------------------

export function useExportSchedule(hallId: string) {
  return useMutation({
    mutationFn: (filters?: ScheduleFilters) => exportSchedulePdf(hallId, filters),
    onSuccess: (blob) => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `maintenance_schedule_${new Date().toISOString().slice(0, 10)}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success("Schedule exported successfully!");
    },
    onError: (error) => {
      toast.error(extractApiError(error) || "Failed to export schedule.");
    },
  });
}
