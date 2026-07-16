"use client";

import { use } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Building2,
  CalendarDays,
  CheckCircle2,
  ClipboardCheck,
  FileImage,
  LogOut,
  MapPin,
  ShieldAlert,
  Wrench,
} from "lucide-react";
import axios from "axios";

import { AuthGuard } from "@/components/shared/auth-guard";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/use-auth";
import { useComplaint } from "@/hooks/use-complaints";
import { ComplaintTimeline } from "@/components/shared/complaint-timeline";
import { LoadingSkeleton } from "@/components/shared/loading-skeleton";
import { NotificationBell } from "@/components/shared/notification-bell";
import { AiPriorityBadge } from "@/components/shared/ai-priority-badge";

// Import broken-down subcomponents
import { ComplaintDetailHeader } from "./complaint-detail-header";
import { AssignmentPanel } from "./assignment-panel";
import { StatusActionBar } from "./status-action-bar";
import { AiWorkerRecommenderCard } from "./ai-worker-recommender-card";
import { resolveImageUrl } from "@/utils/image-url";


interface PageProps {
  params: Promise<{ id: string }>;
}

export default function AdminComplaintDetailPage({ params }: PageProps) {
  const resolvedParams = use(params);
  const id = resolvedParams.id;
  const { user, signOut } = useAuth();

  const { data: complaint, isLoading, error } = useComplaint(id);

  // Format dates
  const formatDate = (dateString?: string | null) => {
    if (!dateString) return "N/A";
    return new Date(dateString).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // Determine error type
  const is404 = axios.isAxiosError(error) && error.response?.status === 404;
  const is403 = axios.isAxiosError(error) && error.response?.status === 403;

  // Extract last update metadata from history
  const lastHistory =
    complaint && complaint.status_history && complaint.status_history.length > 0
      ? complaint.status_history[complaint.status_history.length - 1]
      : null;
  const lastUpdatedBy = lastHistory ? lastHistory.updated_by : "Student Creator";

  return (
    <AuthGuard>
      <div className="flex min-h-screen flex-col bg-background">
        {/* Top nav */}
        <header className="sticky top-0 z-40 border-b border-border/60 bg-background/80 backdrop-blur-xl">
          <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
            <Link href="/dashboard/admin" className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
                <Building2 className="h-4 w-4 text-primary" />
              </div>
              <span className="text-sm font-semibold tracking-tight">IntelliHall Admin</span>
            </Link>

            <div className="flex items-center gap-3">
              <div className="hidden text-right sm:block">
                <p className="text-sm font-medium">{user?.name}</p>
                <p className="text-xs text-muted-foreground">{user?.email}</p>
              </div>
              <Badge variant="default">Hall Admin</Badge>
              <NotificationBell />
              <Button
                variant="ghost"
                size="sm"
                onClick={signOut}
                className="gap-2 text-muted-foreground hover:text-foreground"
              >
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">Sign out</span>
              </Button>
            </div>
          </div>
        </header>

        {/* Main content */}
        <main className="flex-1">
          <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
            {/* Back to Queue */}
            <div className="mb-6">
              <Link
                href="/dashboard/admin/complaints"
                className="inline-flex items-center text-xs font-semibold text-muted-foreground hover:text-foreground gap-1 transition-colors"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                Back to Complaint Queue
              </Link>
            </div>

            {/* Error States */}
            {error && (is404 || is403) ? (
              <Card className="border border-destructive/20 bg-destructive/5 max-w-xl mx-auto mt-12">
                <CardContent className="p-8 text-center flex flex-col items-center justify-center">
                  <ShieldAlert className="h-12 w-12 text-destructive mb-4" />
                  <CardTitle className="text-xl font-bold text-destructive">
                    {is404 ? "Complaint Not Found" : "Access Forbidden"}
                  </CardTitle>
                  <p className="text-sm text-muted-foreground mt-2 max-w-sm">
                    {is404
                      ? "The complaint ID you are trying to view does not exist. It may have been deleted or the link is broken."
                      : "You do not have permission to view this complaint. It belongs to another residential hall."}
                  </p>
                  <Button asChild className="mt-6">
                    <Link href="/dashboard/admin/complaints">Return to Queue</Link>
                  </Button>
                </CardContent>
              </Card>
            ) : error ? (
              <div className="rounded-2xl border border-destructive/20 bg-destructive/5 p-8 text-center text-destructive max-w-xl mx-auto mt-12">
                <p className="font-semibold">Failed to load complaint details</p>
                <p className="text-sm mt-1 opacity-80">
                  {error instanceof Error ? error.message : "Please check your network and try again."}
                </p>
                <Button asChild className="mt-6" variant="outline">
                  <Link href="/dashboard/admin/complaints">Go Back</Link>
                </Button>
              </div>
            ) : isLoading ? (
              <LoadingSkeleton variant="detail" />
            ) : complaint ? (
              <div className="space-y-6">
                {/* Header section */}
                <ComplaintDetailHeader
                  id={complaint.id}
                  title={complaint.title}
                  category={complaint.category}
                  priority={complaint.priority}
                  status={complaint.status}
                  createdAt={complaint.created_at}
                />

                {/* Grid layout */}
                <div className="grid gap-6 md:grid-cols-3">
                  {/* Left layout: Details details */}
                  <div className="space-y-6 md:col-span-2">
                    {/* Description Card */}
                    <Card className="border border-border/50 bg-card">
                      <CardHeader>
                        <CardTitle className="text-sm font-semibold">Description</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm text-foreground/90 whitespace-pre-wrap leading-relaxed">
                          {complaint.description}
                        </p>
                      </CardContent>
                    </Card>

                    {/* Resident Info & Location */}
                    <Card className="border border-border/50 bg-card">
                      <CardHeader>
                        <CardTitle className="text-sm font-semibold flex items-center gap-2">
                          <MapPin className="h-4 w-4 text-primary" />
                          Resident & Location Details
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="grid gap-4 sm:grid-cols-2 text-sm">
                        <div className="p-3 rounded-lg bg-muted/30 border border-border/40">
                          <span className="text-[10px] text-muted-foreground block font-bold uppercase">Student Name</span>
                          <span className="font-semibold text-foreground text-sm">
                            {complaint.student_name || "Unknown Resident"}
                          </span>
                        </div>
                        <div className="p-3 rounded-lg bg-muted/30 border border-border/40">
                          <span className="text-[10px] text-muted-foreground block font-bold uppercase">Complaint Type</span>
                          <span className="font-semibold text-foreground text-sm capitalize">
                            {complaint.complaint_type.replace("_", " ")}
                          </span>
                        </div>

                        {complaint.complaint_type === "personal" ? (
                          <div className="sm:col-span-2 p-3 rounded-lg bg-muted/30 border border-border/40">
                            <span className="text-[10px] text-muted-foreground block font-bold uppercase">Room Number</span>
                            <span className="font-semibold text-foreground text-sm">
                              Room {complaint.room_number || "N/A"}
                            </span>
                          </div>
                        ) : (
                          <>
                            <div className="p-3 rounded-lg bg-muted/30 border border-border/40">
                              <span className="text-[10px] text-muted-foreground block font-bold uppercase">Block / Wing</span>
                              <span className="font-semibold text-foreground text-sm">
                                {complaint.block || "—"}
                              </span>
                            </div>
                            <div className="p-3 rounded-lg bg-muted/30 border border-border/40">
                              <span className="text-[10px] text-muted-foreground block font-bold uppercase">Floor</span>
                              <span className="font-semibold text-foreground text-sm">
                                {complaint.floor || "—"}
                              </span>
                            </div>
                            <div className="p-3 rounded-lg bg-muted/30 border border-border/40">
                              <span className="text-[10px] text-muted-foreground block font-bold uppercase">Common Area</span>
                              <span className="font-semibold text-foreground text-sm">
                                {complaint.common_area || "—"}
                              </span>
                            </div>
                            <div className="p-3 rounded-lg bg-muted/30 border border-border/40">
                              <span className="text-[10px] text-muted-foreground block font-bold uppercase">QR Location ID</span>
                              <span className="font-mono font-semibold text-foreground text-xs">
                                {complaint.qr_location_id || "—"}
                              </span>
                            </div>
                          </>
                        )}
                      </CardContent>
                    </Card>

                    {/* Images Section */}
                    <Card className="border border-border/50 bg-card">
                      <CardHeader>
                        <CardTitle className="text-sm font-semibold flex items-center gap-2">
                          <FileImage className="h-4 w-4 text-primary" />
                          Attached Images
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        {!complaint.images || complaint.images.length === 0 ? (
                          <div className="flex flex-col items-center justify-center p-8 border border-dashed border-border rounded-xl bg-muted/20 text-center min-h-[140px]">
                            <FileImage className="h-8 w-8 text-muted-foreground/60 mb-2.5" />
                            <p className="text-sm font-semibold text-muted-foreground">No images attached.</p>
                            <p className="text-[10px] text-muted-foreground/80 mt-1 max-w-[200px]">
                              The resident student did not upload any pictures for this complaint.
                            </p>
                          </div>
                        ) : (
                          <div className="grid gap-4 grid-cols-2 sm:grid-cols-3">
                            {complaint.images.map((img) => (
                              <div
                                key={img.id}
                                className="relative aspect-square rounded-lg border border-border overflow-hidden bg-muted group"
                              >
                                {/* eslint-disable-next-line @next/next/no-img-element */}
                                <img
                                  src={resolveImageUrl(img.image_url)}
                                  alt="Attachment"
                                  className="object-cover w-full h-full transition-transform group-hover:scale-105"
                                />
                              </div>
                            ))}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </div>

                  {/* Right layout: Sidebar control panels */}
                  <div className="space-y-6">
                    {/* FSM Status Transitions */}
                    <StatusActionBar
                      complaintId={complaint.id}
                      currentStatus={complaint.status}
                      onStatusUpdated={() => {
                        // React Query will automatically refetch via invalidation in the hooks
                      }}
                    />

                    {/* AI Priority Prediction card — shown when AI data is available */}
                    {complaint.predicted_priority && (
                      <AiPriorityBadge
                        studentPriority={complaint.priority}
                        predictedPriority={complaint.predicted_priority}
                        aiConfidence={complaint.ai_confidence}
                        variant="card"
                      />
                    )}

                    {/* AI Worker Recommendation card */}
                    <AiWorkerRecommenderCard complaint={complaint} />


                    {/* Assignment info panel (read-only, shown when scheduled) */}
                    {complaint.assignment && (
                      <Card className="border border-border/50 bg-card">
                        <CardHeader className="pb-3">
                          <CardTitle className="text-sm font-bold flex items-center gap-2">
                            <CalendarDays className="h-4 w-4 text-primary" />
                            Scheduled Assignment
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-2 text-xs">
                          <div className="grid grid-cols-2 gap-y-2">
                            <span className="text-muted-foreground font-medium">Worker:</span>
                            <span className="font-semibold text-foreground">{complaint.assignment.worker_name}</span>
                            <span className="text-muted-foreground font-medium">Type:</span>
                            <span className="font-semibold text-foreground capitalize">{complaint.assignment.worker_type.replace("_", " ")}</span>
                            <span className="text-muted-foreground font-medium">Visit Date:</span>
                            <span className="font-semibold text-foreground">
                              {new Date(complaint.assignment.scheduled_date + "T00:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                            </span>
                            {complaint.assignment.scheduled_time && (
                              <>
                                <span className="text-muted-foreground font-medium">Time Slot:</span>
                                <span className="font-semibold text-foreground">{complaint.assignment.scheduled_time}</span>
                              </>
                            )}
                            {complaint.assignment.admin_remarks && (
                              <>
                                <span className="text-muted-foreground font-medium">Remarks:</span>
                                <span className="font-semibold text-foreground">{complaint.assignment.admin_remarks}</span>
                              </>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    )}

                    {/* Completion slip info panel */}
                    {complaint.completion_slip && (
                      <Card className="border border-border/50 bg-card">
                        <CardHeader className="pb-3">
                          <CardTitle className="text-sm font-bold flex items-center gap-2">
                            <ClipboardCheck className="h-4 w-4 text-emerald-500" />
                            Completion Slip
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-2 text-xs">
                          <div className="grid grid-cols-2 gap-y-2">
                            <span className="text-muted-foreground font-medium">Work Done:</span>
                            <span className="font-semibold text-foreground">{complaint.completion_slip.work_done}</span>
                            <span className="text-muted-foreground font-medium">Completed:</span>
                            <span className="font-semibold text-foreground">
                              {new Date(complaint.completion_slip.completion_date).toLocaleString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                            </span>
                            <span className="text-muted-foreground font-medium">Student:</span>
                            <span className={`font-bold uppercase text-[10px] px-1.5 py-0.5 rounded ${
                              complaint.completion_slip.student_confirmation_status === "confirmed"
                                ? "bg-emerald-500/10 text-emerald-600"
                                : complaint.completion_slip.student_confirmation_status === "rejected"
                                ? "bg-red-500/10 text-red-600"
                                : "bg-amber-500/10 text-amber-600"
                            }`}>
                              {complaint.completion_slip.student_confirmation_status}
                            </span>
                            {complaint.completion_slip.student_comment && (
                              <>
                                <span className="text-muted-foreground font-medium">Student Comment:</span>
                                <span className="font-semibold text-foreground">{complaint.completion_slip.student_comment}</span>
                              </>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    )}

                    {/* Legacy assignment panel (only shown when not yet scheduled) */}
                    {!complaint.assignment && (
                      <AssignmentPanel
                        key={complaint.updated_at}
                        complaintId={complaint.id}
                        initialMaintenanceType={complaint.maintenance_type}
                        initialAssignee={complaint.current_assignee}
                        initialVisitTime={complaint.preferred_visit_time}
                      />
                    )}

                    {/* Timeline card */}
                    <Card className="border border-border/50 bg-card">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-semibold">Timeline & History Logs</CardTitle>
                      </CardHeader>
                      <CardContent className="pt-2 space-y-6">
                        <ComplaintTimeline history={complaint.status_history} />

                        {/* Read-Only Operational Summary */}
                        <div className="pt-4 border-t border-border/40 text-xs space-y-2.5 text-muted-foreground">
                          <p className="font-bold text-[10px] uppercase text-foreground/80 tracking-wider">
                            Operational Summary
                          </p>
                          <div className="grid grid-cols-2 gap-y-2 text-[11px]">
                            <span className="font-medium">Current Status:</span>
                            <span className="text-foreground font-semibold uppercase tracking-wide text-[10px]">
                              {complaint.status}
                            </span>
                            <span className="font-medium">Assigned Worker:</span>
                            <span className="text-foreground font-semibold">
                              {complaint.current_assignee || "Unassigned"}
                            </span>
                            <span className="font-medium">Maintenance Type:</span>
                            <span className="text-foreground font-semibold uppercase text-[10px]">
                              {complaint.maintenance_type || "None"}
                            </span>
                            <span className="font-medium">Preferred Visit Time:</span>
                            <span className="text-foreground font-semibold">
                              {formatDate(complaint.preferred_visit_time)}
                            </span>
                            <span className="font-medium">Last Updated By:</span>
                            <span className="text-foreground font-semibold truncate">
                              {lastUpdatedBy}
                            </span>
                            <span className="font-medium">Last Updated At:</span>
                            <span className="text-foreground font-semibold">
                              {formatDate(complaint.updated_at)}
                            </span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
