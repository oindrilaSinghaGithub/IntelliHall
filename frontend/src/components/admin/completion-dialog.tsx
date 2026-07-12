"use client";

import { useState } from "react";
import { CheckCircle2, Loader2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { useUpdateComplaintStatus } from "@/hooks/use-complaints";
import type { Complaint } from "@/types/complaint";

interface CompletionDialogProps {
  complaintId: string;
  open: boolean;
  onClose: () => void;
  onSuccess: (complaint: Complaint) => void;
}

export function CompletionDialog({
  complaintId,
  open,
  onClose,
  onSuccess,
}: CompletionDialogProps) {
  const [workDone, setWorkDone] = useState("");
  const [adminRemarks, setAdminRemarks] = useState("");
  const [error, setError] = useState("");

  const mutation = useUpdateComplaintStatus(complaintId);

  if (!open) return null;

  const handleSubmit = () => {
    if (!workDone.trim()) {
      setError("Please describe what work was done.");
      return;
    }
    setError("");

    mutation.mutate(
      {
        new_status: "completed",
        work_done: workDone.trim(),
        admin_remarks: adminRemarks.trim() || null,
      },
      {
        onSuccess: (updated) => {
          onSuccess(updated);
          onClose();
        },
      }
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-xs">
      <div className="relative w-full max-w-md rounded-xl border border-border/80 bg-card p-6 shadow-2xl animate-in fade-in-50 zoom-in-95 duration-200">
        {/* Close */}
        <button
          onClick={onClose}
          disabled={mutation.isPending}
          className="absolute right-4 top-4 rounded-md opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-hidden disabled:pointer-events-none"
          aria-label="Close"
        >
          <X className="h-4 w-4" />
        </button>

        {/* Header */}
        <div className="mb-5">
          <h3 className="text-lg font-semibold leading-none tracking-tight text-foreground flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-emerald-500" />
            Mark Repair as Completed
          </h3>
          <p className="text-xs text-muted-foreground mt-1.5">
            Describe what was repaired. The complaint will automatically move to{" "}
            <span className="font-semibold text-foreground">Awaiting Student Confirmation</span>.
          </p>
        </div>

        <div className="space-y-4">
          {/* Work Done */}
          <div className="space-y-1.5">
            <Label htmlFor="work-done" className="text-xs font-bold text-muted-foreground uppercase">
              Work Done <span className="text-destructive">*</span>
            </Label>
            <textarea
              id="work-done"
              rows={4}
              placeholder="Describe what maintenance work was performed…"
              value={workDone}
              onChange={(e) => {
                setWorkDone(e.target.value);
                if (error) setError("");
              }}
              disabled={mutation.isPending}
              className="flex w-full rounded-md border border-input bg-card px-3 py-2 text-sm shadow-xs placeholder:text-muted-foreground focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring disabled:opacity-50 text-foreground"
              aria-invalid={!!error}
            />
            {error && <p className="text-xs text-destructive">{error}</p>}
          </div>

          {/* Admin Remarks */}
          <div className="space-y-1.5">
            <Label htmlFor="completion-remarks" className="text-xs font-bold text-muted-foreground uppercase">
              Admin Remarks <span className="text-muted-foreground font-normal">(optional)</span>
            </Label>
            <textarea
              id="completion-remarks"
              rows={2}
              placeholder="Any additional notes…"
              value={adminRemarks}
              onChange={(e) => setAdminRemarks(e.target.value)}
              disabled={mutation.isPending}
              className="flex w-full rounded-md border border-input bg-card px-3 py-2 text-sm shadow-xs placeholder:text-muted-foreground focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring disabled:opacity-50 text-foreground"
            />
          </div>

          {/* Info note */}
          <div className="rounded-lg bg-blue-500/10 border border-blue-500/20 p-3 text-xs text-blue-600 dark:text-blue-400">
            The student will be notified and asked to confirm the repair from their dashboard.
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-2 mt-6">
          <Button variant="outline" size="sm" onClick={onClose} disabled={mutation.isPending} className="text-xs">
            Cancel
          </Button>
          <Button
            size="sm"
            onClick={handleSubmit}
            disabled={mutation.isPending}
            className="text-xs gap-1.5 bg-emerald-600 hover:bg-emerald-700"
          >
            {mutation.isPending && <Loader2 className="h-3 w-3 animate-spin" />}
            Mark Completed
          </Button>
        </div>
      </div>
    </div>
  );
}
