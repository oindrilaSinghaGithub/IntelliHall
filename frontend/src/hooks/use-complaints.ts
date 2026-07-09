import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import {
  createComplaint,
  getComplaint,
  getMyComplaints,
  getHallComplaints,
  updateComplaintFields,
  updateComplaintStatus,
} from "@/services/complaint";
import type { ComplaintCreateRequest } from "@/types/complaint";
import { extractApiError } from "@/services/api-client";

export const COMPLAINT_KEYS = {
  all: ["complaints"] as const,
  student: (filters?: Record<string, string | number | boolean | null | undefined>) =>
    [...COMPLAINT_KEYS.all, "student", filters || {}] as const,
  hall: (hallId: string, filters?: Record<string, string | number | boolean | null | undefined>) =>
    [...COMPLAINT_KEYS.all, "hall", hallId, filters || {}] as const,
  detail: (id: string) => ["complaint", id] as const,
};

// ---------------------------------------------------------------------------
// Hook: get student's complaints
// ---------------------------------------------------------------------------

export function useComplaints(filters: Record<string, string | number | boolean | null | undefined>) {
  return useQuery({
    queryKey: COMPLAINT_KEYS.student(filters),
    queryFn: () => getMyComplaints(filters),
  });
}

// ---------------------------------------------------------------------------
// Hook: get single complaint detail
// ---------------------------------------------------------------------------

export function useComplaint(id: string) {
  return useQuery({
    queryKey: COMPLAINT_KEYS.detail(id),
    queryFn: () => getComplaint(id),
    enabled: !!id,
    staleTime: 30000, // 30 seconds
  });
}

// ---------------------------------------------------------------------------
// Hook: get hall complaints (Admin queue list)
// ---------------------------------------------------------------------------

export function useHallComplaints(
  hallId: string,
  filters: Record<string, string | number | boolean | null | undefined>
) {
  return useQuery({
    queryKey: COMPLAINT_KEYS.hall(hallId, filters),
    queryFn: () => getHallComplaints(hallId, filters),
    enabled: !!hallId,
    staleTime: 30000, // 30 seconds
  });
}

// ---------------------------------------------------------------------------
// Hook: update complaint details/assignment (Admin only)
// ---------------------------------------------------------------------------

export function useUpdateComplaintFields(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, string | number | boolean | null | undefined>) =>
      updateComplaintFields(id, data),
    onSuccess: (updated) => {
      toast.success("Assignment updated successfully!");
      queryClient.invalidateQueries({ queryKey: COMPLAINT_KEYS.detail(id) });
      queryClient.invalidateQueries({ queryKey: ["complaints", "hall", updated.hall_id] });
    },
    onError: (error) => {
      toast.error(extractApiError(error) || "Failed to update assignment.");
    },
  });
}

// ---------------------------------------------------------------------------
// Hook: update complaint status/FSM transition (Admin only)
// ---------------------------------------------------------------------------

export function useUpdateComplaintStatus(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { new_status: string; remarks?: string | null }) =>
      updateComplaintStatus(id, data),
    onSuccess: (updated) => {
      toast.success("Status updated successfully!");
      queryClient.invalidateQueries({ queryKey: COMPLAINT_KEYS.detail(id) });
      queryClient.invalidateQueries({ queryKey: ["complaints", "hall", updated.hall_id] });
    },
    onError: (error) => {
      toast.error(extractApiError(error) || "Failed to update status.");
    },
  });
}

// ---------------------------------------------------------------------------
// Hook: create a new complaint
// ---------------------------------------------------------------------------

export function useCreateComplaint() {
  const queryClient = useQueryClient();
  const router = useRouter();

  return useMutation({
    mutationFn: (data: ComplaintCreateRequest) => createComplaint(data),
    onSuccess: (newComplaint) => {
      toast.success("Complaint raised successfully!");
      // Invalidate student list queries to trigger reload
      queryClient.invalidateQueries({ queryKey: COMPLAINT_KEYS.student() });
      // Redirect to detail page
      router.push(`/dashboard/complaints/${newComplaint.id}`);
    },
    onError: (error: unknown) => {
      const msg = extractApiError(error);
      toast.error(msg || "Failed to raise complaint.");
    },
  });
}
