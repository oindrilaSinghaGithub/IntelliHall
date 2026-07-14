"use client";

import { useState } from "react";
import { AlertTriangle, Calendar, Loader2, RefreshCw, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { useRescheduleComplaint } from "@/hooks/use-complaints";
import type { Complaint } from "@/types/complaint";

interface VisitFailedCardProps {
  complaint: Complaint;
  onRescheduled?: () => void;
}

export function VisitFailedCard({ complaint, onRescheduled }: VisitFailedCardProps) {
  const [showModal, setShowModal] = useState(false);
  const [visitTime, setVisitTime] = useState("");
  const [timeError, setTimeError] = useState("");

  const rescheduleMutation = useRescheduleComplaint(complaint.id);

  // Pull the most recent VISIT_FAILED entry from history for failure reason
  const failureHistoryEntry = [...(complaint.status_history ?? [])]
    .filter((h) => h.new_status === "visit_failed_room_locked")
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())[0];

  const failureReason = failureHistoryEntry?.remarks ?? null;
  const adminRemarks = complaint.assignment?.admin_remarks ?? null;

  const formatDate = (dateString?: string | null) => {
    if (!dateString) return null;
    return new Date(dateString).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // Compute the minimum allowed datetime-local value (now + 1 minute)
  const getMinDateTime = () => {
    const now = new Date();
    now.setMinutes(now.getMinutes() + 1);
    // datetime-local format: YYYY-MM-DDTHH:MM
    return now.toISOString().slice(0, 16);
  };

  const handleOpenModal = () => {
    setVisitTime("");
    setTimeError("");
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setVisitTime("");
    setTimeError("");
  };

  const handleSubmit = () => {
    if (!visitTime) {
      setTimeError("Please select a preferred visit time.");
      return;
    }

    // Client-side: ensure the chosen time is in the future
    const chosen = new Date(visitTime);
    if (chosen <= new Date()) {
      setTimeError("Please choose a future date and time.");
      return;
    }

    setTimeError("");

    // Convert datetime-local string to ISO 8601 with timezone
    const isoString = chosen.toISOString();

    rescheduleMutation.mutate(
      { preferred_visit_time: isoString },
      {
        onSuccess: () => {
          handleCloseModal();
          onRescheduled?.();
        },
      },
    );
  };

  return (
    <>
      {/* Warning card */}
      <Card className="border border-rose-500/30 bg-rose-500/5">
        <CardContent className="p-5">
          {/* Header */}
          <div className="flex items-start gap-3 mb-4">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-rose-500/10">
              <AlertTriangle className="h-5 w-5 text-rose-500" />
            </div>
            <div>
              <p className="text-sm font-bold text-rose-600 dark:text-rose-400">
                🔒 Maintenance Visit Failed — Room Was Locked
              </p>
              <p className="text-xs text-muted-foreground mt-0.5">
                The maintenance team could not access your room. Please reschedule the visit at a
                time when you will be available.
              </p>
            </div>
          </div>

          {/* Details */}
          <div className="rounded-lg border border-border/40 bg-card p-3 mb-4 space-y-2 text-xs">
            <p className="font-semibold text-foreground truncate">{complaint.title}</p>

            {failureReason && (
              <p className="text-muted-foreground">
                <span className="font-medium text-foreground">Failure reason: </span>
                {failureReason}
              </p>
            )}

            {adminRemarks && (
              <p className="text-muted-foreground">
                <span className="font-medium text-foreground">Admin remarks: </span>
                {adminRemarks}
              </p>
            )}

            {complaint.preferred_visit_time && (
              <p className="text-muted-foreground flex items-center gap-1">
                <Calendar className="h-3 w-3 shrink-0" />
                <span className="font-medium text-foreground">Previous preferred time: </span>
                {formatDate(complaint.preferred_visit_time)}
              </p>
            )}
          </div>

          {/* Action button */}
          <Button
            size="sm"
            className="w-full gap-2 bg-rose-600 hover:bg-rose-700 text-white"
            onClick={handleOpenModal}
            disabled={rescheduleMutation.isPending}
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Reschedule Visit
          </Button>
        </CardContent>
      </Card>

      {/* Reschedule modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-xs">
          <div className="relative w-full max-w-md rounded-xl border border-border/80 bg-card p-6 shadow-2xl animate-in fade-in-50 zoom-in-95 duration-200">
            {/* Close button */}
            <button
              onClick={handleCloseModal}
              disabled={rescheduleMutation.isPending}
              className="absolute right-4 top-4 rounded-md opacity-70 hover:opacity-100 focus:outline-hidden disabled:pointer-events-none"
              aria-label="Close reschedule dialog"
            >
              <X className="h-4 w-4" />
            </button>

            {/* Title */}
            <div className="mb-5">
              <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                <RefreshCw className="h-5 w-5 text-rose-500" />
                Reschedule Maintenance Visit
              </h3>
              <p className="text-xs text-muted-foreground mt-1.5">
                Choose a new preferred time when you will be in your room so the maintenance team
                can complete the visit.
              </p>
            </div>

            {/* Datetime-local input */}
            <div className="space-y-1.5 mb-5">
              <Label
                htmlFor={`reschedule-time-${complaint.id}`}
                className="text-xs font-bold text-muted-foreground uppercase"
              >
                Preferred Visit Time <span className="text-destructive">*</span>
              </Label>
              <input
                id={`reschedule-time-${complaint.id}`}
                type="datetime-local"
                value={visitTime}
                min={getMinDateTime()}
                onChange={(e) => {
                  setVisitTime(e.target.value);
                  if (timeError) setTimeError("");
                }}
                disabled={rescheduleMutation.isPending}
                aria-invalid={!!timeError}
                className="flex h-9 w-full rounded-md border border-input bg-card px-3 py-1 text-sm shadow-xs focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring disabled:opacity-50 text-foreground"
              />
              {timeError && <p className="text-xs text-destructive">{timeError}</p>}
            </div>

            {/* Buttons */}
            <div className="flex items-center justify-end gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleCloseModal}
                disabled={rescheduleMutation.isPending}
                className="text-xs"
              >
                Cancel
              </Button>
              <Button
                size="sm"
                className="text-xs gap-1.5 bg-rose-600 hover:bg-rose-700 text-white"
                onClick={handleSubmit}
                disabled={rescheduleMutation.isPending}
              >
                {rescheduleMutation.isPending && <Loader2 className="h-3 w-3 animate-spin" />}
                <RefreshCw className="h-3 w-3" />
                Reschedule
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
