"use client";

import Link from "next/link";
import { useState } from "react";
import {
  Search,
  Eye,
  ClipboardList,
  Clock,
  Wrench,
  CheckCircle2,
} from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ComplaintStatusBadge } from "@/components/shared/complaint-status-badge";
import type { ComplaintSummary } from "@/types/complaint";

interface AdminComplaintsTableProps {
  complaints: ComplaintSummary[];
}

export function AdminComplaintsTable({ complaints }: AdminComplaintsTableProps) {
  const [searchTerm, setSearchTerm] = useState("");

  // Category formatter
  const formatCategory = (cat: string) => {
    return cat.charAt(0).toUpperCase() + cat.slice(1).replace("_", " ");
  };

  // Date formatter
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
    critical: "bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20",
  };

  // Aggregate local counts for the summary cards
  const totalCount = complaints.length;
  const pendingCount = complaints.filter(
    (c) =>
      c.status === "submitted" ||
      c.status === "verified" ||
      c.status === "scheduled"
  ).length;
  const inProgressCount = complaints.filter((c) => c.status === "in_progress").length;
  const completedCount = complaints.filter(
    (c) => c.status === "completed" || c.status === "closed"
  ).length;

  // Client-side search within the current paginated set
  const filteredComplaints = complaints.filter((c) =>
    c.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Lightweight Summary Cards */}
      <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
        {[
          {
            title: "Total Loaded",
            value: totalCount,
            desc: "On current page",
            icon: ClipboardList,
            color: "text-blue-500 bg-blue-500/10",
          },
          {
            title: "Pending Sync",
            value: pendingCount,
            desc: "Submitted / verified / scheduled",
            icon: Clock,
            color: "text-amber-500 bg-amber-500/10",
          },
          {
            title: "In Progress Sync",
            value: inProgressCount,
            desc: "Actively working on",
            icon: Wrench,
            color: "text-purple-500 bg-purple-500/10",
          },
          {
            title: "Completed Sync",
            value: completedCount,
            desc: "Resolved / closed cases",
            icon: CheckCircle2,
            color: "text-emerald-500 bg-emerald-500/10",
          },
        ].map((card, idx) => (
          <Card key={idx} className="border border-border/50 bg-card">
            <CardContent className="p-4 flex items-start justify-between">
              <div className="space-y-1">
                <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                  {card.title}
                </p>
                <p className="text-xl font-bold tracking-tight">{card.value}</p>
                <p className="text-[9px] text-muted-foreground">{card.desc}</p>
              </div>
              <div className={`p-2 rounded-lg ${card.color}`}>
                <card.icon className="h-4 w-4" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Control Search Bar */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search current page by title..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="flex h-9 w-full rounded-md border border-input bg-card pl-9 pr-3 py-1 text-sm shadow-xs transition-colors placeholder:text-muted-foreground focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 text-foreground"
        />
        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] bg-muted px-1.5 py-0.5 rounded font-medium text-muted-foreground">
          Search current page
        </span>
      </div>

      {/* Responsive Table Grid */}
      <div className="rounded-xl border border-border/50 bg-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-sm text-foreground">
            <thead>
              <tr className="border-b border-border bg-muted/40 font-medium text-muted-foreground">
                <th className="px-4 py-3.5">Title</th>
                <th className="px-4 py-3.5">Student</th>
                <th className="px-4 py-3.5">Location</th>
                <th className="px-4 py-3.5">Category</th>
                <th className="px-4 py-3.5">Type</th>
                <th className="px-4 py-3.5">Priority</th>
                <th className="px-4 py-3.5">Status</th>
                <th className="px-4 py-3.5">Created Date</th>
                <th className="px-4 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/40">
              {filteredComplaints.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-4 py-12 text-center text-muted-foreground">
                    {searchTerm ? (
                      <p>No complaints match your search term on this page.</p>
                    ) : (
                      <p>No complaints registered in this hall.</p>
                    )}
                  </td>
                </tr>
              ) : (
                filteredComplaints.map((c) => {
                  // Format location text based on complaint type
                  const locationText =
                    c.complaint_type === "personal"
                      ? `Room ${c.room_number || "N/A"}`
                      : [c.block, c.floor, c.common_area]
                          .filter(Boolean)
                          .join(", ") || "Common Area";

                  return (
                    <tr key={c.id} className="hover:bg-muted/15 transition-colors">
                      <td className="px-4 py-3.5 font-medium max-w-[180px] truncate">
                        {c.title}
                      </td>
                      <td className="px-4 py-3.5 text-muted-foreground">
                        {c.student_name || "Unknown"}
                      </td>
                      <td className="px-4 py-3.5 text-muted-foreground max-w-[150px] truncate">
                        {locationText}
                      </td>
                      <td className="px-4 py-3.5">
                        <span className="inline-block text-xs font-semibold px-2 py-0.5 rounded bg-muted text-muted-foreground capitalize">
                          {formatCategory(c.category)}
                        </span>
                      </td>
                      <td className="px-4 py-3.5 capitalize text-xs text-muted-foreground">
                        {c.complaint_type.replace("_", " ")}
                      </td>
                      <td className="px-4 py-3.5">
                        <span
                          className={`inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded border uppercase ${
                            priorityStyles[c.priority] || ""
                          }`}
                        >
                          {c.priority}
                        </span>
                      </td>
                      <td className="px-4 py-3.5">
                        <ComplaintStatusBadge status={c.status} />
                      </td>
                      <td className="px-4 py-3.5 text-xs text-muted-foreground">
                        {formatDate(c.created_at)}
                      </td>
                      <td className="px-4 py-3.5 text-right">
                        <Link href={`/dashboard/admin/complaints/${c.id}`} passHref>
                          <Button variant="ghost" size="sm" className="h-8 gap-1.5 text-xs">
                            <Eye className="h-3.5 w-3.5" />
                            View
                          </Button>
                        </Link>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
