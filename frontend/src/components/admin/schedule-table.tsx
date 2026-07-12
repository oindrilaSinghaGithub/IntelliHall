"use client";

import { useRouter } from "next/navigation";
import type { ScheduleItem } from "@/services/schedule";

const STATUS_LABELS: Record<string, string> = {
  scheduled: "Scheduled",
  in_progress: "In Progress",
};

const WORKER_TYPE_LABELS: Record<string, string> = {
  electrician: "Electrician",
  plumber: "Plumber",
  carpenter: "Carpenter",
  mason: "Mason",
  cleaning_staff: "Cleaning Staff",
  civil: "Civil",
  network: "Network",
  housekeeping: "Housekeeping",
  other: "Other",
};

interface ScheduleTableProps {
  items: ScheduleItem[];
}

export function ScheduleTable({ items }: ScheduleTableProps) {
  const router = useRouter();

  if (items.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-border bg-card/60 p-12 text-center">
        <p className="text-sm font-medium text-muted-foreground">
          No scheduled maintenance work found for the selected filters.
        </p>
      </div>
    );
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr + "T00:00:00").toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  return (
    <div className="overflow-x-auto rounded-xl border border-border/50">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border/50 bg-muted/40">
            <th className="px-4 py-3 text-left text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
              Visit Date
            </th>
            <th className="px-4 py-3 text-left text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
              Worker
            </th>
            <th className="px-4 py-3 text-left text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
              Type
            </th>
            <th className="px-4 py-3 text-left text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
              Room
            </th>
            <th className="px-4 py-3 text-left text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
              Complaint
            </th>
            <th className="px-4 py-3 text-left text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
              Status
            </th>
            <th className="px-4 py-3 text-left text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
              Category
            </th>
          </tr>
        </thead>
        <tbody>
          {items.map((item, idx) => (
            <tr
              key={item.complaint_id}
              onClick={() => router.push(`/dashboard/admin/complaints/${item.complaint_id}`)}
              className={`border-b border-border/30 cursor-pointer transition-colors hover:bg-muted/50 ${
                idx % 2 === 0 ? "bg-card" : "bg-muted/10"
              }`}
            >
              <td className="px-4 py-3 font-semibold text-foreground whitespace-nowrap">
                {formatDate(item.visit_date)}
                {item.scheduled_time && (
                  <div className="text-[10px] text-muted-foreground">{item.scheduled_time}</div>
                )}
              </td>
              <td className="px-4 py-3 font-medium text-foreground">{item.worker_name}</td>
              <td className="px-4 py-3">
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-muted text-muted-foreground uppercase">
                  {WORKER_TYPE_LABELS[item.worker_type] ?? item.worker_type}
                </span>
              </td>
              <td className="px-4 py-3 text-foreground">{item.room_number ?? "—"}</td>
              <td className="px-4 py-3 text-foreground max-w-[200px] truncate" title={item.complaint_title}>
                {item.complaint_title}
              </td>
              <td className="px-4 py-3">
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                    item.status === "in_progress"
                      ? "bg-purple-500/10 text-purple-600 dark:text-purple-400"
                      : "bg-blue-500/10 text-blue-600 dark:text-blue-400"
                  }`}
                >
                  {STATUS_LABELS[item.status] ?? item.status}
                </span>
              </td>
              <td className="px-4 py-3">
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-muted text-muted-foreground capitalize">
                  {item.category.replace("_", " ")}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
