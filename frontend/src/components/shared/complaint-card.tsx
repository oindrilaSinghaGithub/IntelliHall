import Link from "next/link";
import { Calendar, ChevronRight, AlertTriangle } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { ComplaintStatusBadge } from "./complaint-status-badge";
import type { ComplaintSummary } from "@/types/complaint";

interface ComplaintCardProps {
  complaint: ComplaintSummary;
}

export function ComplaintCard({ complaint }: ComplaintCardProps) {
  // Format Category
  const formatCategory = (cat: string) => {
    return cat.charAt(0).toUpperCase() + cat.slice(1).replace("_", " ");
  };

  // Format Date
  const formatDate = (dateString: string) => {
    const d = new Date(dateString);
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  // Priority Styles
  const priorityStyles: Record<string, string> = {
    low: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20",
    medium: "bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 border-yellow-500/20",
    high: "bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/20",
    critical: "bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20 animate-pulse",
  };

  return (
    <Link href={`/dashboard/complaints/${complaint.id}`} className="block group">
      <Card className="overflow-hidden border border-border/50 bg-card transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-md">
        <CardContent className="p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div className="space-y-2.5 flex-1">
              <div className="flex flex-wrap items-center gap-2 text-xs">
                <span className="font-semibold px-2 py-0.5 rounded bg-muted text-muted-foreground uppercase tracking-wider">
                  {formatCategory(complaint.category)}
                </span>
                <span className={`inline-flex items-center gap-1 font-semibold px-2 py-0.5 rounded border ${priorityStyles[complaint.priority]}`}>
                  {complaint.priority === "critical" && (
                    <AlertTriangle className="h-3 w-3 shrink-0" />
                  )}
                  {complaint.priority.toUpperCase()}
                </span>
              </div>
              
              <h3 className="text-base font-semibold text-foreground group-hover:text-primary transition-colors line-clamp-1">
                {complaint.title}
              </h3>

              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Calendar className="h-3.5 w-3.5 shrink-0" />
                <span>Raised on {formatDate(complaint.created_at)}</span>
              </div>
            </div>

            <div className="flex items-center justify-between sm:flex-col sm:items-end sm:justify-center gap-3 border-t border-border/40 pt-3 sm:border-0 sm:pt-0 shrink-0">
              <ComplaintStatusBadge status={complaint.status} />
              <div className="hidden sm:flex items-center text-xs font-medium text-muted-foreground group-hover:text-primary transition-colors gap-1">
                View details
                <ChevronRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
