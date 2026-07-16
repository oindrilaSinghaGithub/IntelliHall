export type WorkerSpecialization =
  | "electrician"
  | "plumber"
  | "carpenter"
  | "cleaning_staff"
  | "network_staff"
  | "civil_maintenance";

export type WorkerAvailability = "available" | "busy" | "on_leave";

export type WorkerExperienceLevel = "junior" | "intermediate" | "senior";

export interface Worker {
  id: string;
  name: string;
  phone: string;
  specialization: WorkerSpecialization;
  availability_status: WorkerAvailability;
  skill_rating: number;
  experience_years: number;
  experience_level: WorkerExperienceLevel;
  completed_jobs: number;
  active_jobs: number;
  hall_id: string;
  created_at: string;
  updated_at: string;
}

export interface WorkerCreateRequest {
  name: string;
  phone: string;
  specialization: WorkerSpecialization;
  availability_status?: WorkerAvailability;
  skill_rating?: number;
  experience_years?: number;
  experience_level?: WorkerExperienceLevel;
}

export interface WorkerUpdateRequest {
  name?: string;
  phone?: string;
  specialization?: WorkerSpecialization;
  availability_status?: WorkerAvailability;
  skill_rating?: number;
  experience_years?: number;
  experience_level?: WorkerExperienceLevel;
}

export interface PaginatedWorkerResponse {
  items: Worker[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}
