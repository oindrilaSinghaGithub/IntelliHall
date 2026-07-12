"use client";

import { useState } from "react";
import { AlertTriangle, CheckCircle2, Loader2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { useConfirmRepair, useRejectRepair } from "@/hooks/use-complaints";
import type { Complaint } from "@/types/complaint";

interface StudentConfirmationCardProps {
  complaint: Complaint;
  onConfirmed: () => void;
  onRejected: () => void;
}

export function StudentConfirmationCard({
  complaint,
  onConfirmed,
  onRejected,
}: StudentConfirmationCardProps) {
  const [comment, setComment] = useState("");
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [rejectComment, setRejectComment] = useState("");
  const [rejectError, setRejectError] = useState("");

  const confirmMutation = useConfirmRepair(complaint.id);
  const rejectMutation = useRejectRepair(complaint.id);

  const slip = complaint.completion_slip;

  const handleConfirm = () => {
    confirmMutation.mutate(comment || null, {
      onSuccess: onConfirmed,
    });
  };

  const handleRejectSubmit = () => {
    if (!rejectComment.trim()) {
      setRejectError("Please describe the issue with the repair.");
      return;
    }
    setRejectError("");
    rejectMutation.mutate(rejectComment.trim(), {
      onSuccess: () => {
        setShowRejectModal(false);
        onRejected();
      },
    });
  };

  return (
    <>
      <Card className="border border-amber-500/30 bg-amber-500/5">
        <CardContent className="p-5">
          {/* Header */}
          <div className="flex items-start gap-3 mb-4">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-amber-500/10">
              <AlertTriangle className="h-5 w-5 text-amber-500" />
            </div>
            <div>
              <p className="text-sm font-bold text-amber-600 dark:text-amber-400">
                ⚠ Your Confirmation is Required
              </p>
              <p className="text-xs text-muted-foreground mt-0.5">
                The maintenance team has marked this repair as complete. Please confirm whether the issue was resolved.
              </p>
            </div>
          </div>

          {/* Complaint info */}
          <div className="rounded-lg border border-border/40 bg-card p-3 mb-4 space-y-1.5 text-xs">
            <p className="font-semibold text-foreground truncate">{complaint.title}</p>
            {slip && (
              <>
                <p className="text-muted-foreground">
                  <span className="font-medium text-foreground">Worker:</span>{" "}
                  {slip.worker_name} ({slip.worker_type.replace("_", " ")})
                </p>
                <p className="text-muted-foreground">
                  <span className="font-medium text-foreground">Work done:</span>{" "}
                  {slip.work_done}
                </p>
                {slip.admin_remarks && (
                  <p className="text-muted-foreground">
                    <span className="font-medium text-foreground">Admin remarks:</span>{" "}
                    {slip.admin_remarks}
                  </p>
                )}
              </>
            )}
          </div>

          {/* Optional confirm comment */}
          <div className="space-y-1.5 mb-4">
            <Label htmlFor={`confirm-comment-${complaint.id}`} className="text-xs font-bold text-muted-foreground uppercase">
              Comment (optional)
            </Label>
            <textarea
              id={`confirm-comment-${complaint.id}`}
              rows={2}
              placeholder="Any comments about the repair?"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              disabled={confirmMutation.isPending}
              className="flex w-full rounded-md border border-input bg-card px-3 py-2 text-sm shadow-xs placeholder:text-muted-foreground focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring disabled:opacity-50 text-foreground"
            />
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-3">
            <Button
              size="sm"
              className="flex-1 gap-1.5 text-xs bg-emerald-600 hover:bg-emerald-700"
              onClick={handleConfirm}
              disabled={confirmMutation.isPending || rejectMutation.isPending}
            >
              {confirmMutation.isPending ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <CheckCircle2 className="h-3.5 w-3.5" />
              )}
              Repair is Done
            </Button>
            <Button
              size="sm"
              variant="destructive"
              className="flex-1 gap-1.5 text-xs"
              onClick={() => setShowRejectModal(true)}
              disabled={confirmMutation.isPending || rejectMutation.isPending}
            >
              <AlertTriangle className="h-3.5 w-3.5" />
              Issue Persists
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Reject modal */}
      {showRejectModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-xs">
          <div className="relative w-full max-w-md rounded-xl border border-border/80 bg-card p-6 shadow-2xl animate-in fade-in-50 zoom-in-95 duration-200">
            <button
              onClick={() => {
                setShowRejectModal(false);
                setRejectComment("");
                setRejectError("");
              }}
              disabled={rejectMutation.isPending}
              className="absolute right-4 top-4 rounded-md opacity-70 hover:opacity-100 focus:outline-hidden disabled:pointer-events-none"
              aria-label="Close"
            >
              <X className="h-4 w-4" />
            </button>

            <div className="mb-4">
              <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-destructive" />
                Report Unresolved Issue
              </h3>
              <p className="text-xs text-muted-foreground mt-1.5">
                Please describe the problem so the admin can re-schedule the repair.
              </p>
            </div>

            <div className="space-y-1.5 mb-5">
              <Label htmlFor="reject-comment" className="text-xs font-bold text-muted-foreground uppercase">
                What is still wrong? <span className="text-destructive">*</span>
              </Label>
              <textarea
                id="reject-comment"
                rows={4}
                placeholder="Describe what was not fixed or what still needs attention…"
                value={rejectComment}
                onChange={(e) => {
                  setRejectComment(e.target.value);
                  if (rejectError) setRejectError("");
                }}
                disabled={rejectMutation.isPending}
                className="flex w-full rounded-md border border-input bg-card px-3 py-2 text-sm shadow-xs placeholder:text-muted-foreground focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring disabled:opacity-50 text-foreground"
                aria-invalid={!!rejectError}
              />
              {rejectError && <p className="text-xs text-destructive">{rejectError}</p>}
            </div>

            <div className="flex items-center justify-end gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setShowRejectModal(false);
                  setRejectComment("");
                  setRejectError("");
                }}
                disabled={rejectMutation.isPending}
                className="text-xs"
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                size="sm"
                onClick={handleRejectSubmit}
                disabled={rejectMutation.isPending}
                className="text-xs gap-1.5"
              >
                {rejectMutation.isPending && <Loader2 className="h-3 w-3 animate-spin" />}
                Submit Report
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
