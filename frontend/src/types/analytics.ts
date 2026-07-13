import { ComplaintCategory, ComplaintStatus, ComplaintSummary } from "./complaint";

export interface AnalyticsSummary {
  total_complaints: number;
  open_complaints: number;
  in_progress: number;
  completed: number;
  critical_complaints: number;
  complaints_today: number;
  complaints_this_week: number;
  avg_resolution_time_hours: number | null;
}

export interface CategoryCount {
  category: ComplaintCategory;
  count: number;
}

export interface StatusCount {
  status: ComplaintStatus;
  count: number;
}

export interface MonthlyTrendPoint {
  month: string;
  count: number;
}

export interface HallAnalytics {
  hall_id: string;
  hall_name: string;
  summary: AnalyticsSummary;
  by_category: CategoryCount[];
  by_status: StatusCount[];
  monthly_trend: MonthlyTrendPoint[];
  recent_complaints: ComplaintSummary[];
}
