import { apiClient } from "@/services/api-client";
import type {
  Notification,
  PaginatedNotificationResponse,
  UnreadCountResponse,
} from "@/types/notification";

// ---------------------------------------------------------------------------
// GET /api/v1/notifications/
// ---------------------------------------------------------------------------

export async function getNotifications(params?: {
  page?: number;
  page_size?: number;
  unread_only?: boolean;
}): Promise<PaginatedNotificationResponse> {
  const response = await apiClient.get<PaginatedNotificationResponse>("/notifications/", {
    params,
  });
  return response.data;
}

// ---------------------------------------------------------------------------
// GET /api/v1/notifications/unread-count
// ---------------------------------------------------------------------------

export async function getUnreadCount(): Promise<UnreadCountResponse> {
  const response = await apiClient.get<UnreadCountResponse>("/notifications/unread-count");
  return response.data;
}

// ---------------------------------------------------------------------------
// PATCH /api/v1/notifications/{id}/read
// ---------------------------------------------------------------------------

export async function markNotificationRead(id: string): Promise<Notification> {
  const response = await apiClient.patch<Notification>(`/notifications/${id}/read`);
  return response.data;
}

// ---------------------------------------------------------------------------
// PATCH /api/v1/notifications/read-all
// ---------------------------------------------------------------------------

export async function markAllRead(): Promise<{ marked_read: number }> {
  const response = await apiClient.patch<{ marked_read: number }>("/notifications/read-all");
  return response.data;
}
