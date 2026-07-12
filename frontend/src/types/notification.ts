export interface Notification {
  id: string;
  user_id: string;
  complaint_id: string | null;
  message: string;
  is_read: boolean;
  created_at: string;
}

export interface PaginatedNotificationResponse {
  items: Notification[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
  unread_count: number;
}

export interface UnreadCountResponse {
  unread_count: number;
}
