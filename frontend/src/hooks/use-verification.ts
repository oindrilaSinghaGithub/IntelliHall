import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import {
  approveVerification,
  getPendingVerifications,
  rejectVerification,
  updateMyHall,
} from "@/services/verification";
import { extractApiError } from "@/services/api-client";
import { getMe } from "@/services/auth";
import { useAuthStore } from "@/store/auth-store";
import type { UpdateHallRequest } from "@/types/auth";

// ---------------------------------------------------------------------------
// Query keys
// ---------------------------------------------------------------------------

export const VERIFICATION_KEYS = {
  all: ["verifications"] as const,
  pending: (params?: { page?: number; page_size?: number }) =>
    [...VERIFICATION_KEYS.all, "pending", params ?? {}] as const,
};

// ---------------------------------------------------------------------------
// Hook: list pending verification requests (admin)
// ---------------------------------------------------------------------------

export function usePendingVerifications(params?: { page?: number; page_size?: number }) {
  return useQuery({
    queryKey: VERIFICATION_KEYS.pending(params),
    queryFn: () => getPendingVerifications(params),
    staleTime: 30_000,
  });
}

// ---------------------------------------------------------------------------
// Hook: approve a student's verification (admin)
// ---------------------------------------------------------------------------

export function useApproveVerification() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (userId: string) => approveVerification(userId),
    onSuccess: () => {
      toast.success("Student hall affiliation approved.");
      queryClient.invalidateQueries({ queryKey: VERIFICATION_KEYS.all });
    },
    onError: (error: unknown) => {
      toast.error(extractApiError(error) || "Failed to approve verification.");
    },
  });
}

// ---------------------------------------------------------------------------
// Hook: reject a student's verification (admin)
// ---------------------------------------------------------------------------

export function useRejectVerification() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ userId, reason }: { userId: string; reason?: string | null }) =>
      rejectVerification(userId, reason),
    onSuccess: () => {
      toast.success("Verification request rejected.");
      queryClient.invalidateQueries({ queryKey: VERIFICATION_KEYS.all });
    },
    onError: (error: unknown) => {
      toast.error(extractApiError(error) || "Failed to reject verification.");
    },
  });
}

// ---------------------------------------------------------------------------
// Hook: student updates their own hall (triggers re-verification)
// ---------------------------------------------------------------------------

export function useUpdateMyHall() {
  const setUser = useAuthStore((s) => s.setUser);
  return useMutation({
    mutationFn: (data: UpdateHallRequest) => updateMyHall(data),
    onSuccess: async () => {
      // Refresh the user in the Zustand store so hall_verification_status
      // immediately reflects "pending" in the UI without a page reload.
      try {
        const freshUser = await getMe();
        setUser(freshUser);
      } catch {
        // silently ignore — the next page load will refresh it
      }
      toast.success(
        "Hall updated. Your affiliation is now pending re-verification by the Hall Office."
      );
    },
    onError: (error: unknown) => {
      toast.error(extractApiError(error) || "Failed to update hall.");
    },
  });
}
