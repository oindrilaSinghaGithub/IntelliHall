import { Badge } from "@/components/ui/badge";
import type { ComplaintStatus } from "@/types/complaint";

interface ComplaintStatusBadgeProps {
  status: ComplaintStatus;
}

export function ComplaintStatusBadge({ status }: ComplaintStatusBadgeProps) {
  // Map backend status to human readable labels
  const labelMap: Record<ComplaintStatus, string> = {
    submitted: "Submitted",
    verified: "Verified",
    scheduled: "Scheduled",
    in_progress: "In Progress",
    completed: "Completed",
    waiting_student_confirmation: "Awaiting Confirmation",
    closed: "Closed",
    visit_failed_room_locked: "Visit Failed (Locked)",
  };

  // Map backend status to distinct styled classes
  // Using oklch colors mapped through classes or direct style injections for maximum flexibility and beauty.
  const styleMap: Record<ComplaintStatus, string> = {
    submitted: "bg-blue-500/10 text-blue-500 hover:bg-blue-500/15 border-blue-500/20",
    verified: "bg-indigo-500/10 text-indigo-500 hover:bg-indigo-500/15 border-indigo-500/20",
    scheduled: "bg-purple-500/10 text-purple-500 hover:bg-purple-500/15 border-purple-500/20",
    in_progress: "bg-amber-500/10 text-amber-500 hover:bg-amber-500/15 border-amber-500/20",
    completed: "bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/15 border-emerald-500/20",
    waiting_student_confirmation: "bg-orange-500/10 text-orange-500 hover:bg-orange-500/15 border-orange-500/20",
    closed: "bg-slate-500/10 text-slate-400 hover:bg-slate-500/15 border-slate-500/20",
    visit_failed_room_locked: "bg-rose-500/10 text-rose-500 hover:bg-rose-500/15 border-rose-500/20",
  };

  return (
    <Badge
      variant="outline"
      className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
        styleMap[status] || "bg-secondary text-secondary-foreground"
      }`}
    >
      {labelMap[status] || status}
    </Badge>
  );
}
