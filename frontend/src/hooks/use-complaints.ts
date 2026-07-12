import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import {
  confirmRepair,
  createComplaint,
  getComplaint,
  getMyComplaints,
  getHallComplaints,
  rejectRepair,
  updateComplaintFields,
  updateComplaintStatus,
} from "@/services/complaint";
import type { ComplaintCreateRequest, StatusUpdateRequest } from "@/types/complaint";
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
// Extended to accept full StatusUpdateRequest including scheduling fields.
// ---------------------------------------------------------------------------

export function useUpdateComplaintStatus(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: StatusUpdateRequest) => updateComplaintStatus(id, data),
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
      queryClient.invalidateQueries({ queryKey: COMPLAINT_KEYS.student() });
      router.push(`/dashboard/complaints/${newComplaint.id}`);
    },
    onError: (error: unknown) => {
      const msg = extractApiError(error);
      toast.error(msg || "Failed to raise complaint.");
    },
  });
}

// ---------------------------------------------------------------------------
// Hook: student confirms repair
// ---------------------------------------------------------------------------

export function useConfirmRepair(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (comment?: string | null) => confirmRepair(id, comment),
    onSuccess: () => {
      toast.success("Repair confirmed! Thank you for the feedback.");
      queryClient.invalidateQueries({ queryKey: COMPLAINT_KEYS.detail(id) });
      queryClient.invalidateQueries({ queryKey: COMPLAINT_KEYS.student() });
    },
    onError: (error) => {
      toast.error(extractApiError(error) || "Failed to confirm repair.");
    },
  });
}

// ---------------------------------------------------------------------------
// Hook: student rejects repair
// ---------------------------------------------------------------------------

export function useRejectRepair(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (comment: string) => rejectRepair(id, comment),
    onSuccess: () => {
      toast.success("Repair issue reported. The complaint has been reopened.");
      queryClient.invalidateQueries({ queryKey: COMPLAINT_KEYS.detail(id) });
      queryClient.invalidateQueries({ queryKey: COMPLAINT_KEYS.student() });
    },
    onError: (error) => {
      toast.error(extractApiError(error) || "Failed to report issue.");
    },
  });
}
