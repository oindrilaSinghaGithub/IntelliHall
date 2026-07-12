"use client";

import { useState } from "react";
import { AlertCircle, ArrowRight, CheckCircle2, ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { RemarksDialog } from "./remarks-dialog";
import { AssignmentDialog } from "@/components/admin/assignment-dialog";
import { CompletionDialog } from "@/components/admin/completion-dialog";
import { useUpdateComplaintStatus } from "@/hooks/use-complaints";
import type { Complaint, ComplaintStatus } from "@/types/complaint";

interface TransitionConfig {
  primary: ComplaintStatus | null;
  secondary: ComplaintStatus | null;
}

const FSM_TRANSITIONS: Record<ComplaintStatus, TransitionConfig> = {
  submitted: { primary: "verified", secondary: "visit_failed_room_locked" },
  verified: { primary: "scheduled", secondary: "visit_failed_room_locked" },
  scheduled: { primary: "in_progress", secondary: "visit_failed_room_locked" },
  in_progress: { primary: "completed", secondary: "visit_failed_room_locked" },
  completed: { primary: "waiting_student_confirmation", secondary: "visit_failed_room_locked" },
  waiting_student_confirmation: { primary: "closed", secondary: "visit_failed_room_locked" },
  reopened: { primary: "verified", secondary: null },
  closed: { primary: null, secondary: null },
  visit_failed_room_locked: { primary: null, secondary: null },
};

const STATUS_LABELS: Record<ComplaintStatus, string> = {
  submitted: "Submitted",
  verified: "Verify Complaint",
  scheduled: "Schedule Visit",
  in_progress: "Start Work (In Progress)",
  completed: "Mark Completed",
  waiting_student_confirmation: "Request Student Confirmation",
  reopened: "Re-verify",
  closed: "Close Ticket",
  visit_failed_room_locked: "Visit Failed (Room Locked)",
};

// Statuses that need a special dialog instead of the plain remarks dialog
const NEEDS_ASSIGNMENT_DIALOG: ComplaintStatus[] = ["scheduled"];
const NEEDS_COMPLETION_DIALOG: ComplaintStatus[] = ["completed"];

interface StatusActionBarProps {
  complaintId: string;
  currentStatus: ComplaintStatus;
  onStatusUpdated?: (complaint: Complaint) => void;
}

export function StatusActionBar({
  complaintId,
  currentStatus,
  onStatusUpdated,
}: StatusActionBarProps) {
  const [selectedTarget, setSelectedTarget] = useState<ComplaintStatus | null>(null);
  const [showAssignmentDialog, setShowAssignmentDialog] = useState(false);
  const [showCompletionDialog, setShowCompletionDialog] = useState(false);

  const updateStatusMutation = useUpdateComplaintStatus(complaintId);

  const config = FSM_TRANSITIONS[currentStatus] || { primary: null, secondary: null };
  const hasTransitions = config.primary !== null || config.secondary !== null;

  const handleOpenDialog = (target: ComplaintStatus) => {
    if (NEEDS_ASSIGNMENT_DIALOG.includes(target)) {
      setShowAssignmentDialog(true);
    } else if (NEEDS_COMPLETION_DIALOG.includes(target)) {
      setShowCompletionDialog(true);
    } else {
      setSelectedTarget(target);
    }
  };

  const handleCloseDialog = () => setSelectedTarget(null);

  const handleConfirmTransition = (remarks: string) => {
    if (!selectedTarget) return;
    updateStatusMutation.mutate(
      { new_status: selectedTarget, remarks: remarks.trim() || null },
      { onSuccess: () => handleCloseDialog() }
    );
  };

  const getDialogDetails = (target: ComplaintStatus | null) => {
    if (!target) return { title: "", desc: "", btn: "Confirm" };
    if (target === "visit_failed_room_locked") {
      return {
        title: "Record Visit Failure",
        desc: "You are marking this visit as failed because the room was locked. Please provide a reason or notes for the student resident.",
        btn: "Record Failure",
      };
    }
    if (target === "closed") {
      return {
        title: "Close Complaint",
        desc: "Close this complaint as fully resolved. This requires student confirmation to have been given.",
        btn: "Close Complaint",
      };
    }
    return {
      title: `Advance to: ${STATUS_LABELS[target] || target}`,
      desc: `Transition this complaint from '${currentStatus}' to '${target}'. You may add optional remarks below.`,
      btn: "Confirm Transition",
    };
  };

  const dialogDetails = getDialogDetails(selectedTarget);

  return (
    <div className="space-y-4">
      {/* Informational banners */}
      {currentStatus === "waiting_student_confirmation" && (
        <Card className="border border-blue-500/20 bg-blue-500/5">
          <CardContent className="p-4 flex items-start gap-3">
            <CheckCircle2 className="h-5 w-5 text-blue-500 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-blue-600 dark:text-blue-400">
                Awaiting Student Confirmation
              </p>
              <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
                The repair has been marked complete. The student must confirm the fix before you can close the ticket.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {currentStatus === "visit_failed_room_locked" && (
        <Card className="border border-rose-500/20 bg-rose-500/5">
          <CardContent className="p-4 flex items-start gap-3">
            <ShieldAlert className="h-5 w-5 text-rose-500 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-rose-600 dark:text-rose-400">
                Visit Failed — Room Locked
              </p>
              <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
                The student must coordinate a new time or re-raise a ticket.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {currentStatus === "closed" && (
        <Card className="border border-muted-foreground/20 bg-muted/30">
          <CardContent className="p-4 flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-muted-foreground shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-muted-foreground">Ticket Closed</p>
              <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
                This complaint has been resolved and closed.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Action Buttons */}
      {hasTransitions && (
        <Card className="border border-border/50 bg-card">
          <CardContent className="p-4">
            <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-3">
              Workflow Status Controls
            </p>
            <div className="flex flex-col gap-2.5">
              {config.primary && (
                <Button
                  variant="default"
                  size="sm"
                  className="w-full justify-between text-xs font-semibold shadow-xs"
                  onClick={() => handleOpenDialog(config.primary!)}
                  disabled={updateStatusMutation.isPending}
                >
                  <span className="flex items-center gap-1.5">
                    ⚙ {STATUS_LABELS[config.primary] || config.primary}
                  </span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              )}
              {config.secondary && (
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full justify-between text-xs border-red-200 text-red-600 hover:bg-red-50 hover:text-red-700 hover:border-red-300 dark:border-red-900/30 dark:text-red-400 dark:hover:bg-red-950/20"
                  onClick={() => handleOpenDialog(config.secondary!)}
                  disabled={updateStatusMutation.isPending}
                >
                  <span className="flex items-center gap-1.5">
                    ⚠ {STATUS_LABELS[config.secondary] || config.secondary}
                  </span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Plain remarks dialog (for non-special transitions) */}
      <RemarksDialog
        key={selectedTarget || "none"}
        isOpen={selectedTarget !== null}
        onClose={handleCloseDialog}
        onConfirm={handleConfirmTransition}
        title={dialogDetails.title}
        description={dialogDetails.desc}
        confirmText={dialogDetails.btn}
        isLoading={updateStatusMutation.isPending}
      />

      {/* Assignment dialog — for SCHEDULED transition */}
      <AssignmentDialog
        complaintId={complaintId}
        open={showAssignmentDialog}
        onClose={() => setShowAssignmentDialog(false)}
        onSuccess={(complaint) => {
          setShowAssignmentDialog(false);
          onStatusUpdated?.(complaint);
        }}
      />

      {/* Completion dialog — for COMPLETED transition */}
      <CompletionDialog
        complaintId={complaintId}
        open={showCompletionDialog}
        onClose={() => setShowCompletionDialog(false)}
        onSuccess={(complaint) => {
          setShowCompletionDialog(false);
          onStatusUpdated?.(complaint);
        }}
      />
    </div>
  );
}
