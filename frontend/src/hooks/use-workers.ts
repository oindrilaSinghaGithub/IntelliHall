import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import {
  createWorker,
  listWorkers,
  updateWorker,
  deleteWorker,
} from "@/services/worker";
import { extractApiError } from "@/services/api-client";
import type {
  WorkerCreateRequest,
  WorkerUpdateRequest,
} from "@/types/worker";

// ---------------------------------------------------------------------------
// Query keys
// ---------------------------------------------------------------------------

export const WORKER_KEYS = {
  all: ["workers"] as const,
  list: (params?: { page?: number; page_size?: number }) =>
    [...WORKER_KEYS.all, "list", params ?? {}] as const,
};

// ---------------------------------------------------------------------------
// Hook: list workers in admin's hall
// ---------------------------------------------------------------------------

export function useWorkers(params?: { page?: number; page_size?: number }) {
  return useQuery({
    queryKey: WORKER_KEYS.list(params),
    queryFn: () => listWorkers(params),
    staleTime: 10_000, // 10 seconds cache validity
  });
}

// ---------------------------------------------------------------------------
// Hook: create a worker (admin)
// ---------------------------------------------------------------------------

export function useCreateWorker() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: WorkerCreateRequest) => createWorker(data),
    onSuccess: () => {
      toast.success("Worker added to hall staff registry.");
      queryClient.invalidateQueries({ queryKey: WORKER_KEYS.all });
    },
    onError: (error: unknown) => {
      toast.error(extractApiError(error) || "Failed to add worker.");
    },
  });
}

// ---------------------------------------------------------------------------
// Hook: update worker details/status (admin)
// ---------------------------------------------------------------------------

export function useUpdateWorker() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: WorkerUpdateRequest }) =>
      updateWorker(id, data),
    onSuccess: () => {
      toast.success("Worker details updated successfully.");
      queryClient.invalidateQueries({ queryKey: WORKER_KEYS.all });
    },
    onError: (error: unknown) => {
      toast.error(extractApiError(error) || "Failed to update worker.");
    },
  });
}

// ---------------------------------------------------------------------------
// Hook: delete worker (admin)
// ---------------------------------------------------------------------------

export function useDeleteWorker() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteWorker(id),
    onSuccess: () => {
      toast.success("Worker removed from registry.");
      queryClient.invalidateQueries({ queryKey: WORKER_KEYS.all });
    },
    onError: (error: unknown) => {
      toast.error(
        extractApiError(error) ||
          "Failed to delete worker. They may have active assignments."
      );
    },
  });
}
