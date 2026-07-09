import { CheckCircle2, Clock, User, ClipboardList } from "lucide-react";
import type { ComplaintStatusHistory } from "@/types/complaint";

interface ComplaintTimelineProps {
  history: ComplaintStatusHistory[];
}

export function ComplaintTimeline({ history }: ComplaintTimelineProps) {
  // Sort history by timestamp descending (newest first) or ascending (oldest first)?
  // Usually, a timeline shows oldest to newest (ascending) or newest to oldest.
  // Let's sort ascending so it reads like a history book from top to bottom.
  const sortedHistory = [...history].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  const formatDateTime = (dateString: string) => {
    const d = new Date(dateString);
    return d.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getStatusLabel = (status: string) => {
    return status.charAt(0).toUpperCase() + status.slice(1).replace(/_/g, " ");
  };

  if (!sortedHistory.length) {
    return (
      <div className="flex flex-col items-center justify-center py-6 text-center text-muted-foreground text-sm">
        <ClipboardList className="h-8 w-8 mb-2 opacity-40" />
        No status history available.
      </div>
    );
  }

  return (
    <div className="flow-root">
      <ul role="list" className="-mb-8">
        {sortedHistory.map((item, idx) => {
          const isLast = idx === sortedHistory.length - 1;
          const isInitial = item.previous_status === null;

          return (
            <li key={item.id}>
              <div className="relative pb-8">
                {!isLast && (
                  <span
                    className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-border"
                    aria-hidden="true"
                  />
                )}
                <div className="relative flex space-x-3">
                  <div>
                    <span className={`flex h-8 w-8 items-center justify-center rounded-full ring-8 ring-card ${
                      isLast
                        ? "bg-primary/10 text-primary"
                        : "bg-muted text-muted-foreground"
                    }`}>
                      {isLast ? (
                        <CheckCircle2 className="h-4 w-4 shrink-0" />
                      ) : (
                        <Clock className="h-4 w-4 shrink-0" />
                      )}
                    </span>
                  </div>
                  <div className="flex-1 min-w-0 pt-1.5">
                    <div className="text-sm">
                      <p className="font-semibold text-foreground">
                        {isInitial ? (
                          <span>Complaint Submitted</span>
                        ) : (
                          <span>
                            Status updated to{" "}
                            <span className="text-primary font-bold">
                              {getStatusLabel(item.new_status)}
                            </span>
                          </span>
                        )}
                      </p>
                      <div className="mt-1 flex flex-wrap items-center gap-x-2.5 gap-y-1 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <User className="h-3 w-3 shrink-0" />
                          {item.updated_by === "system" ? "System" : `Admin (${item.updated_by.slice(0, 8)})`}
                        </span>
                        <span>•</span>
                        <span>{formatDateTime(item.timestamp)}</span>
                      </div>
                      {item.remarks && (
                        <div className="mt-2 text-sm text-muted-foreground bg-muted/40 p-2.5 rounded-lg border border-border/40">
                          {item.remarks}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
