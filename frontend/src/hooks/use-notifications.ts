import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import {
  getNotifications,
  getUnreadCount,
  markAllRead,
  markNotificationRead,
} from "@/services/notification";
import { extractApiError } from "@/services/api-client";

export const NOTIFICATION_KEYS = {
  all: ["notifications"] as const,
  list: (params?: object) => [...NOTIFICATION_KEYS.all, "list", params || {}] as const,
  unread: () => [...NOTIFICATION_KEYS.all, "unread"] as const,
};

// ---------------------------------------------------------------------------
// Hook: get paginated notifications
// ---------------------------------------------------------------------------

export function useNotifications(params?: {
  page?: number;
  page_size?: number;
  unread_only?: boolean;
}) {
  return useQuery({
    queryKey: NOTIFICATION_KEYS.list(params),
    queryFn: () => getNotifications(params),
    staleTime: 15000,
  });
}

// ---------------------------------------------------------------------------
// Hook: get unread count (polls every 30 seconds)
// ---------------------------------------------------------------------------

export function useUnreadCount() {
  return useQuery({
    queryKey: NOTIFICATION_KEYS.unread(),
    queryFn: getUnreadCount,
    refetchInterval: 30000,
    staleTime: 10000,
  });
}

// ---------------------------------------------------------------------------
// Hook: mark one notification as read
// ---------------------------------------------------------------------------

export function useMarkNotificationRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => markNotificationRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: NOTIFICATION_KEYS.all });
    },
    onError: (error) => {
      toast.error(extractApiError(error) || "Failed to mark notification as read.");
    },
  });
}

// ---------------------------------------------------------------------------
// Hook: mark all notifications as read
// ---------------------------------------------------------------------------

export function useMarkAllRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: markAllRead,
    onSuccess: (data) => {
      if (data.marked_read > 0) {
        toast.success(`Marked ${data.marked_read} notification(s) as read.`);
      }
      queryClient.invalidateQueries({ queryKey: NOTIFICATION_KEYS.all });
    },
    onError: (error) => {
      toast.error(extractApiError(error) || "Failed to mark all notifications as read.");
    },
  });
}
