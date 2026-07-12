"use client";

import { useState } from "react";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import {
  Building2,
  LogOut,
  CheckCircle2,
  XCircle,
  Users,
  Mail,
  Hash,
  Home,
  ChevronLeft,
  ChevronRight,
  Loader2,
  ShieldCheck,
} from "lucide-react";

import { AuthGuard } from "@/components/shared/auth-guard";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/hooks/use-auth";
import { usePendingVerifications, useApproveVerification, useRejectVerification } from "@/hooks/use-verification";
import type { VerificationRequestRead } from "@/types/auth";

// ---------------------------------------------------------------------------
// Single verification card
// ---------------------------------------------------------------------------

function VerificationCard({ student }: { student: VerificationRequestRead }) {
  const [showRejectForm, setShowRejectForm] = useState(false);
  const [rejectReason, setRejectReason] = useState("");

  const approveMutation = useApproveVerification();
  const rejectMutation = useRejectVerification();

  const isActioning = approveMutation.isPending || rejectMutation.isPending;
  const timeAgo = formatDistanceToNow(new Date(student.created_at), { addSuffix: true });

  function handleApprove() {
    approveMutation.mutate(student.id);
  }

  function handleReject() {
    rejectMutation.mutate({
      userId: student.id,
      reason: rejectReason.trim() || null,
    });
    setShowRejectForm(false);
    setRejectReason("");
  }

  return (
    <Card className="border border-border/60 bg-card shadow-xs">
      <CardContent className="p-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          {/* Student info */}
          <div className="space-y-2 min-w-0">
            <div className="flex items-center gap-2">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
                {student.name.charAt(0).toUpperCase()}
              </div>
              <div className="min-w-0">
                <p className="text-sm font-semibold truncate">{student.name}</p>
                <p className="text-xs text-muted-foreground">Registered {timeAgo}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-1.5 sm:grid-cols-2 text-xs text-muted-foreground">
              <span className="flex items-center gap-1.5">
                <Mail className="h-3 w-3 shrink-0" />
                <span className="truncate">{student.email}</span>
              </span>
              {student.roll_number && (
                <span className="flex items-center gap-1.5">
                  <Hash className="h-3 w-3 shrink-0" />
                  {student.roll_number}
                </span>
              )}
              {student.hall_name && (
                <span className="flex items-center gap-1.5">
                  <Building2 className="h-3 w-3 shrink-0" />
                  {student.hall_name}
                </span>
              )}
              {student.room_number && (
                <span className="flex items-center gap-1.5">
                  <Home className="h-3 w-3 shrink-0" />
                  Room {student.room_number}
                </span>
              )}
            </div>
          </div>

          {/* Action buttons */}
          {!showRejectForm && (
            <div className="flex shrink-0 gap-2">
              <Button
                size="sm"
                onClick={handleApprove}
                disabled={isActioning}
                className="gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white"
              >
                {approveMutation.isPending ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <CheckCircle2 className="h-3.5 w-3.5" />
                )}
                Approve
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setShowRejectForm(true)}
                disabled={isActioning}
                className="gap-1.5 border-destructive/40 text-destructive hover:bg-destructive/5 hover:text-destructive"
              >
                <XCircle className="h-3.5 w-3.5" />
                Reject
              </Button>
            </div>
          )}
        </div>

        {/* Inline reject form */}
        {showRejectForm && (
          <>
            <Separator className="my-4" />
            <div className="space-y-3">
              <p className="text-xs font-medium text-muted-foreground">
                Rejection reason{" "}
                <span className="font-normal">(optional — will be shown to the student)</span>
              </p>
              <textarea
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="e.g. Room number provided does not match our records..."
                rows={3}
                className="flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              />
              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={handleReject}
                  disabled={rejectMutation.isPending}
                  variant="destructive"
                  className="gap-1.5"
                >
                  {rejectMutation.isPending ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <XCircle className="h-3.5 w-3.5" />
                  )}
                  Confirm Rejection
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => { setShowRejectForm(false); setRejectReason(""); }}
                  disabled={rejectMutation.isPending}
                >
                  Cancel
                </Button>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function VerificationsPage() {
  const { user, signOut } = useAuth();
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const { data, isLoading, isError } = usePendingVerifications({ page, page_size: pageSize });

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
              <span className="text-sm font-semibold tracking-tight">IntelliHall</span>
            </Link>

            <div className="flex items-center gap-3">
              <div className="hidden text-right sm:block">
                <p className="text-sm font-medium">{user?.name}</p>
                <p className="text-xs text-muted-foreground">{user?.email}</p>
              </div>
              <Badge variant="default">Hall Admin</Badge>
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
          <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
            {/* Page header */}
            <div className="mb-8 flex items-start gap-4">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-primary/10">
                <ShieldCheck className="h-6 w-6 text-primary" />
              </div>
              <div>
                  <h1 className="text-2xl font-bold">Student Hall Verification Requests</h1>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Review and approve or reject student hall affiliation requests for{" "}
                    <span className="font-medium text-foreground">{user?.hall_name ?? "your hall"}</span>.
                    Only student accounts appear here — Hall Admin accounts are automatically verified.
                  </p>
              </div>
            </div>

            {/* Nav breadcrumb */}
            <nav className="mb-6">
              <Link
                href="/dashboard/admin"
                className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-primary transition-colors"
              >
                <ChevronLeft className="h-3 w-3" />
                Back to Admin Dashboard
              </Link>
            </nav>

            {/* Content */}
            {isLoading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="h-28 animate-pulse rounded-xl border border-border/40 bg-muted/30"
                  />
                ))}
              </div>
            ) : isError ? (
              <Card className="border border-destructive/30 bg-destructive/5">
                <CardContent className="p-6 text-center">
                  <p className="text-sm text-destructive font-medium">Failed to load verification requests.</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Make sure you are logged in as a Hall Admin and try again.
                  </p>
                </CardContent>
              </Card>
            ) : !data || data.items.length === 0 ? (
              <Card className="border border-dashed border-border/60">
                <CardContent className="py-16 text-center">
                  <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900/30">
                    <CheckCircle2 className="h-7 w-7 text-emerald-600 dark:text-emerald-400" />
                  </div>
                  <p className="text-base font-semibold">All caught up!</p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    There are no pending hall verification requests for your hall.
                  </p>
                </CardContent>
              </Card>
            ) : (
              <>
                {/* Count */}
                <div className="mb-4 flex items-center gap-2">
                  <Users className="h-4 w-4 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">
                    <span className="font-semibold text-foreground">{data.total}</span>{" "}
                    pending request{data.total !== 1 ? "s" : ""}
                  </p>
                </div>

                {/* Cards */}
                <div className="space-y-4">
                  {data.items.map((student) => (
                    <VerificationCard key={student.id} student={student} />
                  ))}
                </div>

                {/* Pagination */}
                {data.total_pages > 1 && (
                  <div className="mt-8 flex items-center justify-center gap-3">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                      className="gap-1.5"
                    >
                      <ChevronLeft className="h-3.5 w-3.5" />
                      Previous
                    </Button>
                    <span className="text-sm text-muted-foreground">
                      Page {page} of {data.total_pages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                      disabled={page === data.total_pages}
                      className="gap-1.5"
                    >
                      Next
                      <ChevronRight className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                )}
              </>
            )}
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
