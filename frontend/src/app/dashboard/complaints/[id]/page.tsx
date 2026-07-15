"use client";

import { use } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Building2,
  Calendar,
  CalendarDays,
  CheckCircle2,
  ClipboardCheck,
  FileImage,
  LogOut,
  MapPin,
  Clock,
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
import { ComplaintStatusBadge } from "@/components/shared/complaint-status-badge";
import { ComplaintTimeline } from "@/components/shared/complaint-timeline";
import { LoadingSkeleton } from "@/components/shared/loading-skeleton";
import { NotificationBell } from "@/components/shared/notification-bell";
import { StudentConfirmationCard } from "@/components/shared/student-confirmation-card";
import { VisitFailedCard } from "@/components/shared/visit-failed-card";
import { AiPriorityBadge } from "@/components/shared/ai-priority-badge";
import { resolveImageUrl } from "@/utils/image-url";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function ComplaintDetailPage({ params }: PageProps) {
  const resolvedParams = use(params);
  const id = resolvedParams.id;
  const { user, signOut } = useAuth();

  const { data: complaint, isLoading, error } = useComplaint(id);

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

  const formatCategory = (cat?: string) => {
    if (!cat) return "";
    return cat.charAt(0).toUpperCase() + cat.slice(1).replace("_", " ");
  };

  const is404 = axios.isAxiosError(error) && error.response?.status === 404;
  const is403 = axios.isAxiosError(error) && error.response?.status === 403;

  return (
    <AuthGuard>
      <div className="flex min-h-screen flex-col bg-background">
        {/* Top nav */}
        <header className="sticky top-0 z-40 border-b border-border/60 bg-background/80 backdrop-blur-xl">
          <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
            <Link href="/dashboard" className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
                <Building2 className="h-4 w-4 text-primary" />
              </div>
              <span className="text-sm font-semibold tracking-tight">IntelliHall</span>
            </Link>

            <div className="flex items-center gap-3">
              <div className="hidden text-right sm:block">
                <p className="text-sm font-medium">{user?.name}</p>
                <p className="text-xs text-muted-foreground">{user?.email}</p>
              </div>
              <Badge variant={user?.role === "hall_admin" ? "default" : "secondary"}>
                {user?.role === "hall_admin" ? "Hall Admin" : "Student"}
              </Badge>
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
            <div className="mb-6">
              <Link
                href="/dashboard/complaints"
                className="inline-flex items-center text-xs font-medium text-muted-foreground hover:text-primary gap-1 transition-colors"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                Back to My Complaints
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
                      ? "This complaint does not exist or the link is broken."
                      : "You do not have permission to view this complaint."}
                  </p>
                  <Button asChild className="mt-6">
                    <Link href="/dashboard/complaints">Return to My Complaints</Link>
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
                  <Link href="/dashboard/complaints">Go Back</Link>
                </Button>
              </div>
            ) : isLoading ? (
              <LoadingSkeleton variant="detail" />
            ) : complaint ? (
              <div className="space-y-6">
                {/* Visit-failed card — shown when room was locked during maintenance visit */}
                {complaint.status === "visit_failed_room_locked" && (
                  <VisitFailedCard
                    complaint={complaint}
                    onRescheduled={() => {}}
                  />
                )}

                {/* Confirmation card — prominent banner when awaiting student input */}
                {complaint.status === "waiting_student_confirmation" && (
                  <StudentConfirmationCard
                    complaint={complaint}
                    onConfirmed={() => {}}
                    onRejected={() => {}}
                  />
                )}

                {/* Header */}
                <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between border-b border-border/40 pb-6">
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-semibold px-2.5 py-0.5 rounded bg-muted text-muted-foreground text-xs uppercase tracking-wider">
                        {formatCategory(complaint.category)}
                      </span>
                      <span className={`inline-flex font-semibold px-2.5 py-0.5 rounded text-xs border uppercase ${
                        complaint.priority === "critical"
                          ? "bg-red-500/10 text-red-500 border-red-500/20"
                          : complaint.priority === "high"
                          ? "bg-orange-500/10 text-orange-500 border-orange-500/20"
                          : complaint.priority === "medium"
                          ? "bg-yellow-500/10 text-yellow-500 border-yellow-500/20"
                          : "bg-blue-500/10 text-blue-500 border-blue-500/20"
                      }`}>
                        {complaint.priority} Priority
                      </span>
                      <span className="text-xs text-muted-foreground font-medium px-2 py-0.5">
                        ID: <span className="font-mono">{complaint.id.slice(0, 8)}…</span>
                      </span>
                    </div>
                    {/* AI Priority inline badge — shows when AI data available */}
                    {complaint.predicted_priority && (
                      <div className="mt-1">
                        <AiPriorityBadge
                          studentPriority={complaint.priority}
                          predictedPriority={complaint.predicted_priority}
                          aiConfidence={complaint.ai_confidence}
                          variant="inline"
                        />
                      </div>
                    )}
                    <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
                      {complaint.title}
                    </h1>
                    <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                      <Calendar className="h-4 w-4 shrink-0" />
                      <span>Raised on {formatDate(complaint.created_at)}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <ComplaintStatusBadge status={complaint.status} />
                  </div>
                </div>

                {/* Grid layout */}
                <div className="grid gap-6 md:grid-cols-3">
                  {/* Left: details */}
                  <div className="space-y-6 md:col-span-2">
                    {/* Description */}
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

                    {/* Location */}
                    <Card className="border border-border/50 bg-card">
                      <CardHeader>
                        <CardTitle className="text-sm font-semibold flex items-center gap-2">
                          <MapPin className="h-4 w-4 text-primary" />
                          Location Details
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="grid gap-4 sm:grid-cols-2 text-sm">
                        {complaint.complaint_type === "personal" ? (
                          <div className="sm:col-span-2 p-3 rounded-lg bg-muted/30 border border-border/40">
                            <span className="text-xs text-muted-foreground block font-medium">Room Number</span>
                            <span className="font-semibold text-foreground">{complaint.room_number || "Not specified"}</span>
                          </div>
                        ) : (
                          <>
                            {[
                              { label: "Block / Wing", value: complaint.block },
                              { label: "Floor", value: complaint.floor },
                              { label: "Common Area", value: complaint.common_area },
                              { label: "QR Location ID", value: complaint.qr_location_id },
                            ].map(({ label, value }) => (
                              <div key={label} className="p-3 rounded-lg bg-muted/30 border border-border/40">
                                <span className="text-xs text-muted-foreground block font-medium">{label}</span>
                                <span className="font-semibold text-foreground">{value || "—"}</span>
                              </div>
                            ))}
                          </>
                        )}
                      </CardContent>
                    </Card>

                    {/* Scheduled Assignment — shown when scheduled or beyond */}
                    {complaint.assignment && (
                      <Card className="border border-border/50 bg-card">
                        <CardHeader>
                          <CardTitle className="text-sm font-semibold flex items-center gap-2">
                            <CalendarDays className="h-4 w-4 text-primary" />
                            Scheduled Visit
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="grid gap-3 sm:grid-cols-2 text-sm">
                          <div className="p-3 rounded-lg bg-muted/30 border border-border/40">
                            <span className="text-xs text-muted-foreground block font-medium">Worker</span>
                            <span className="font-semibold text-foreground">{complaint.assignment.worker_name}</span>
                          </div>
                          <div className="p-3 rounded-lg bg-muted/30 border border-border/40">
                            <span className="text-xs text-muted-foreground block font-medium">Type</span>
                            <span className="font-semibold text-foreground capitalize">{complaint.assignment.worker_type.replace("_", " ")}</span>
                          </div>
                          <div className="p-3 rounded-lg bg-muted/30 border border-border/40">
                            <span className="text-xs text-muted-foreground block font-medium">Visit Date</span>
                            <span className="font-semibold text-foreground">
                              {new Date(complaint.assignment.scheduled_date + "T00:00:00").toLocaleDateString("en-US", {
                                month: "short", day: "numeric", year: "numeric",
                              })}
                            </span>
                          </div>
                          {complaint.assignment.scheduled_time && (
                            <div className="p-3 rounded-lg bg-muted/30 border border-border/40">
                              <span className="text-xs text-muted-foreground block font-medium">Time Slot</span>
                              <span className="font-semibold text-foreground">{complaint.assignment.scheduled_time}</span>
                            </div>
                          )}
                          {complaint.assignment.admin_remarks && (
                            <div className="sm:col-span-2 p-3 rounded-lg bg-muted/30 border border-border/40">
                              <span className="text-xs text-muted-foreground block font-medium">Admin Remarks</span>
                              <span className="font-semibold text-foreground">{complaint.assignment.admin_remarks}</span>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    )}

                    {/* Completion Slip — shown once repair is marked done */}
                    {complaint.completion_slip && (
                      <Card className="border border-border/50 bg-card">
                        <CardHeader>
                          <CardTitle className="text-sm font-semibold flex items-center gap-2">
                            <ClipboardCheck className="h-4 w-4 text-emerald-500" />
                            Completion Slip
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="grid gap-3 sm:grid-cols-2 text-sm">
                          <div className="sm:col-span-2 p-3 rounded-lg bg-muted/30 border border-border/40">
                            <span className="text-xs text-muted-foreground block font-medium">Work Done</span>
                            <span className="font-semibold text-foreground">{complaint.completion_slip.work_done}</span>
                          </div>
                          <div className="p-3 rounded-lg bg-muted/30 border border-border/40">
                            <span className="text-xs text-muted-foreground block font-medium">Completed On</span>
                            <span className="font-semibold text-foreground">
                              {new Date(complaint.completion_slip.completion_date).toLocaleDateString("en-US", {
                                month: "short", day: "numeric", year: "numeric",
                              })}
                            </span>
                          </div>
                          <div className="p-3 rounded-lg bg-muted/30 border border-border/40">
                            <span className="text-xs text-muted-foreground block font-medium">Confirmation Status</span>
                            <span className={`font-bold text-xs uppercase px-1.5 py-0.5 rounded ${
                              complaint.completion_slip.student_confirmation_status === "confirmed"
                                ? "bg-emerald-500/10 text-emerald-600"
                                : complaint.completion_slip.student_confirmation_status === "rejected"
                                ? "bg-red-500/10 text-red-600"
                                : "bg-amber-500/10 text-amber-600"
                            }`}>
                              {complaint.completion_slip.student_confirmation_status}
                            </span>
                          </div>
                          {complaint.completion_slip.student_comment && (
                            <div className="sm:col-span-2 p-3 rounded-lg bg-muted/30 border border-border/40">
                              <span className="text-xs text-muted-foreground block font-medium">Your Comment</span>
                              <span className="font-semibold text-foreground">{complaint.completion_slip.student_comment}</span>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    )}

                    {/* Legacy assignment card (fallback when no structured assignment) */}
                    {!complaint.assignment && (
                      <Card className="border border-border/50 bg-card">
                        <CardHeader>
                          <CardTitle className="text-sm font-semibold flex items-center gap-2">
                            <Wrench className="h-4 w-4 text-primary" />
                            Maintenance Assignment
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="grid gap-4 sm:grid-cols-2 text-sm">
                          <div className="p-3 rounded-lg bg-muted/30 border border-border/40">
                            <span className="text-xs text-muted-foreground block font-medium">Assignee Name</span>
                            <span className="font-semibold text-foreground">{complaint.current_assignee || "Unassigned"}</span>
                          </div>
                          <div className="p-3 rounded-lg bg-muted/30 border border-border/40">
                            <span className="text-xs text-muted-foreground block font-medium">Worker Type</span>
                            <span className="font-semibold text-foreground uppercase text-xs">{complaint.maintenance_type || "None"}</span>
                          </div>
                          <div className="sm:col-span-2 p-3 rounded-lg bg-muted/30 border border-border/40 flex items-start gap-2.5">
                            <Clock className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
                            <div>
                              <span className="text-xs text-muted-foreground block font-medium">Preferred Visit Time</span>
                              <span className="font-semibold text-foreground text-xs">
                                {complaint.preferred_visit_time ? formatDate(complaint.preferred_visit_time) : "No preference specified"}
                              </span>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    )}

                    {/* Images */}
                    <Card className="border border-border/50 bg-card">
                      <CardHeader>
                        <CardTitle className="text-sm font-semibold flex items-center gap-2">
                          <FileImage className="h-4 w-4 text-primary" />
                          Attached Images
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        {!complaint.images || complaint.images.length === 0 ? (
                          <p className="text-xs text-muted-foreground">No images attached to this complaint.</p>
                        ) : (
                          <div className="grid gap-4 grid-cols-2 sm:grid-cols-3">
                            {complaint.images.map((img) => (
                              <div key={img.id} className="relative aspect-square rounded-lg border border-border overflow-hidden bg-muted group">
                                {/* eslint-disable-next-line @next/next/no-img-element */}
                                <img src={resolveImageUrl(img.image_url)} alt="Attachment" className="object-cover w-full h-full transition-transform group-hover:scale-105" />
                              </div>
                            ))}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </div>

                  {/* Right: timeline */}
                  <div className="space-y-6">
                    <Card className="border border-border/50 bg-card h-fit">
                      <CardHeader>
                        <CardTitle className="text-sm font-semibold">Timeline & History</CardTitle>
                      </CardHeader>
                      <CardContent className="pt-2">
                        <ComplaintTimeline history={complaint.status_history} />
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
