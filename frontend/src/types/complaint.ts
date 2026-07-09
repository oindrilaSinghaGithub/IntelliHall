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
  | "closed"
  | "visit_failed_room_locked";

export type MaintenanceType =
  | "electrician"
  | "plumber"
  | "carpenter"
  | "civil"
  | "network"
  | "housekeeping"
  | "other";

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
