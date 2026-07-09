"use client";

import { Calendar } from "lucide-react";
import { ComplaintStatusBadge } from "@/components/shared/complaint-status-badge";
import type { ComplaintStatus, ComplaintPriority, ComplaintCategory } from "@/types/complaint";

interface ComplaintDetailHeaderProps {
  id: string;
  title: string;
  category: ComplaintCategory;
  priority: ComplaintPriority;
  status: ComplaintStatus;
  createdAt: string;
}

export function ComplaintDetailHeader({
  id,
  title,
  category,
  priority,
  status,
  createdAt,
}: ComplaintDetailHeaderProps) {
  // Format Date
  const formatDate = (dateString: string) => {
    const d = new Date(dateString);
    return d.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const formatCategory = (cat: string) => {
    return cat.charAt(0).toUpperCase() + cat.slice(1).replace("_", " ");
  };

  // Priority Styles
  const priorityStyles: Record<ComplaintPriority, string> = {
    low: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20",
    medium: "bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 border-yellow-500/20",
    high: "bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/20",
    critical: "bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20 animate-pulse",
  };

  return (
    <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between border-b border-border/40 pb-6">
      <div className="space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          {/* Category Tag */}
          <span className="font-semibold px-2.5 py-0.5 rounded bg-muted text-muted-foreground text-xs uppercase tracking-wider">
            {formatCategory(category)}
          </span>
          {/* Priority Tag */}
          <span
            className={`inline-flex font-semibold px-2.5 py-0.5 rounded text-xs border uppercase ${
              priorityStyles[priority] || ""
            }`}
          >
            {priority} Priority
          </span>
          {/* ID Segment */}
          <span className="text-xs text-muted-foreground font-medium px-2 py-0.5">
            ID: <span className="font-mono">{id.slice(0, 8)}...</span>
          </span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
          {title}
        </h1>
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Calendar className="h-4 w-4 shrink-0" />
          <span>Raised on {formatDate(createdAt)}</span>
        </div>
      </div>

      <div className="flex items-center gap-3 shrink-0">
        <ComplaintStatusBadge status={status} />
      </div>
    </div>
  );
}
