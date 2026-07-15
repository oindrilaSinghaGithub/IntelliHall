export type ComplaintType = "personal" | "common_area";

export type ComplaintCategory =
  | "electrical"
  | "plumbing"
  | "carpentry"
  | "civil"
  | "internet"
  | "cleanliness"
  | "water"
  | "furniture"
  | "other";

export type ComplaintPriority = "low" | "medium" | "high" | "critical";

export type ComplaintStatus =
  | "submitted"
  | "verified"
  | "scheduled"
  | "in_progress"
  | "completed"
  | "waiting_student_confirmation"
  | "reopened"
  | "closed"
  | "visit_failed_room_locked";

export type MaintenanceType =
  | "electrician"
  | "plumber"
  | "carpenter"
  | "mason"
  | "cleaning_staff"
  | "civil"
  | "network"
  | "housekeeping"
  | "other";

export type StudentConfirmationStatus = "pending" | "confirmed" | "rejected";

export interface ComplaintAssignment {
  id: string;
  complaint_id: string;
  worker_name: string;
  worker_type: MaintenanceType;
  scheduled_date: string;
  scheduled_time: string | null;
  admin_remarks: string | null;
  created_at: string;
  updated_at: string;
}

export interface CompletionSlip {
  id: string;
  complaint_id: string;
  hall_id: string;
  room_number: string | null;
  worker_name: string;
  worker_type: MaintenanceType;
  completion_date: string;
  work_done: string;
  admin_remarks: string | null;
  student_comment: string | null;
  student_confirmation_status: StudentConfirmationStatus;
  student_confirmation_time: string | null;
  created_at: string;
  updated_at: string;
}

export interface ComplaintImage {
  id: string;
  complaint_id: string;
  image_url: string;
  uploaded_at: string;
}

export interface ComplaintStatusHistory {
  id: string;
  complaint_id: string;
  previous_status: ComplaintStatus | null;
  new_status: ComplaintStatus;
  updated_by: string;
  remarks: string | null;
  timestamp: string;
}

export interface Complaint {
  id: string;
  title: string;
  description: string;
  complaint_type: ComplaintType;
  category: ComplaintCategory;
  priority: ComplaintPriority;
  status: ComplaintStatus;
  maintenance_type: MaintenanceType | null;
  current_assignee: string | null;
  hall_id: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  room_number: string | null;
  block: string | null;
  floor: string | null;
  common_area: string | null;
  qr_location_id: string | null;
  preferred_visit_time: string | null;
  images: ComplaintImage[];
  status_history: ComplaintStatusHistory[];
  student_name?: string | null;
  assignment?: ComplaintAssignment | null;
  completion_slip?: CompletionSlip | null;
  predicted_priority?: ComplaintPriority | null;
  ai_confidence?: number | null;
  affected_count?: number;
  is_affected?: boolean;
  reporter_room?: string | null;
}

export interface ComplaintSummary {
  id: string;
  title: string;
  priority: ComplaintPriority;
  status: ComplaintStatus;
  category: ComplaintCategory;
  created_at: string;
  complaint_type: ComplaintType;
  room_number?: string | null;
  block?: string | null;
  floor?: string | null;
  common_area?: string | null;
  student_name?: string | null;
  predicted_priority?: ComplaintPriority | null;
  ai_confidence?: number | null;
  affected_count?: number;
  is_affected?: boolean;
  reporter_room?: string | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface ComplaintCreateRequest {
  title: string;
  description: string;
  complaint_type: ComplaintType;
  category: ComplaintCategory;
  priority: ComplaintPriority;
  room_number?: string | null;
  block?: string | null;
  floor?: string | null;
  common_area?: string | null;
  qr_location_id?: string | null;
  preferred_visit_time?: string | null;
}

export interface StatusUpdateRequest {
  new_status: string;
  remarks?: string | null;
  // Assignment fields (required when new_status == "scheduled")
  worker_name?: string | null;
  worker_type?: MaintenanceType | null;
  scheduled_date?: string | null;
  scheduled_time?: string | null;
  admin_remarks?: string | null;
  // Completion field (required when new_status == "completed")
  work_done?: string | null;
}

export interface RescheduleRequest {
  /** ISO 8601 datetime string. Must be a future timestamp. */
  preferred_visit_time: string;
}
