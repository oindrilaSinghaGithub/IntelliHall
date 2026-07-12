"use client";

import { useState } from "react";
import { CalendarDays, Loader2, UserCheck, Wrench, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useUpdateComplaintStatus } from "@/hooks/use-complaints";
import type { Complaint, MaintenanceType } from "@/types/complaint";

const MAINTENANCE_TYPES: { value: MaintenanceType; label: string }[] = [
  { value: "electrician", label: "Electrician" },
  { value: "plumber", label: "Plumber" },
  { value: "carpenter", label: "Carpenter" },
  { value: "mason", label: "Mason" },
  { value: "cleaning_staff", label: "Cleaning Staff" },
  { value: "civil", label: "Civil" },
  { value: "network", label: "Network" },
  { value: "housekeeping", label: "Housekeeping" },
  { value: "other", label: "Other" },
];

interface AssignmentDialogProps {
  complaintId: string;
  open: boolean;
  onClose: () => void;
  onSuccess: (complaint: Complaint) => void;
}

export function AssignmentDialog({
  complaintId,
  open,
  onClose,
  onSuccess,
}: AssignmentDialogProps) {
  const [workerName, setWorkerName] = useState("");
  const [workerType, setWorkerType] = useState<MaintenanceType | "">("");
  const [scheduledDate, setScheduledDate] = useState("");
  const [scheduledTime, setScheduledTime] = useState("");
  const [adminRemarks, setAdminRemarks] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  const mutation = useUpdateComplaintStatus(complaintId);

  if (!open) return null;

  const validate = () => {
    const e: Record<string, string> = {};
    if (!workerName.trim()) e.workerName = "Worker name is required.";
    if (!workerType) e.workerType = "Worker type is required.";
    if (!scheduledDate) e.scheduledDate = "Visit date is required.";
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = () => {
    if (!validate()) return;

    mutation.mutate(
      {
        new_status: "scheduled",
        worker_name: workerName.trim(),
        worker_type: workerType as MaintenanceType,
        scheduled_date: scheduledDate,
        scheduled_time: scheduledTime.trim() || null,
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
        {/* Header */}
        <button
          onClick={onClose}
          disabled={mutation.isPending}
          className="absolute right-4 top-4 rounded-md opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-hidden disabled:pointer-events-none"
          aria-label="Close"
        >
          <X className="h-4 w-4" />
        </button>

        <div className="mb-5">
          <h3 className="text-lg font-semibold leading-none tracking-tight text-foreground flex items-center gap-2">
            <CalendarDays className="h-5 w-5 text-primary" />
            Schedule Maintenance Visit
          </h3>
          <p className="text-xs text-muted-foreground mt-1.5">
            Assign a worker and set a visit date to schedule this complaint.
          </p>
        </div>

        <div className="space-y-4">
          {/* Worker Name */}
          <div className="space-y-1.5">
            <Label htmlFor="worker-name" className="text-xs font-bold text-muted-foreground uppercase flex items-center gap-1">
              <UserCheck className="h-3 w-3" /> Worker Name <span className="text-destructive">*</span>
            </Label>
            <Input
              id="worker-name"
              placeholder="e.g. Ramesh Kumar"
              value={workerName}
              onChange={(e) => setWorkerName(e.target.value)}
              disabled={mutation.isPending}
              aria-invalid={!!errors.workerName}
            />
            {errors.workerName && (
              <p className="text-xs text-destructive">{errors.workerName}</p>
            )}
          </div>

          {/* Worker Type */}
          <div className="space-y-1.5">
            <Label htmlFor="worker-type" className="text-xs font-bold text-muted-foreground uppercase flex items-center gap-1">
              <Wrench className="h-3 w-3" /> Worker Type <span className="text-destructive">*</span>
            </Label>
            <select
              id="worker-type"
              value={workerType}
              onChange={(e) => setWorkerType(e.target.value as MaintenanceType)}
              disabled={mutation.isPending}
              className="flex h-9 w-full rounded-md border border-input bg-card px-3 py-1 text-sm shadow-xs text-foreground focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring"
              aria-invalid={!!errors.workerType}
            >
              <option value="">Select worker type…</option>
              {MAINTENANCE_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
            {errors.workerType && (
              <p className="text-xs text-destructive">{errors.workerType}</p>
            )}
          </div>

          {/* Visit Date */}
          <div className="space-y-1.5">
            <Label htmlFor="scheduled-date" className="text-xs font-bold text-muted-foreground uppercase flex items-center gap-1">
              <CalendarDays className="h-3 w-3" /> Visit Date <span className="text-destructive">*</span>
            </Label>
            <input
              id="scheduled-date"
              type="date"
              value={scheduledDate}
              onChange={(e) => setScheduledDate(e.target.value)}
              disabled={mutation.isPending}
              min={new Date().toISOString().split("T")[0]}
              className="flex h-9 w-full rounded-md border border-input bg-card px-3 py-1 text-sm shadow-xs text-foreground focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring"
              aria-invalid={!!errors.scheduledDate}
            />
            {errors.scheduledDate && (
              <p className="text-xs text-destructive">{errors.scheduledDate}</p>
            )}
          </div>

          {/* Time Slot (optional) */}
          <div className="space-y-1.5">
            <Label htmlFor="scheduled-time" className="text-xs font-bold text-muted-foreground uppercase">
              Time Slot <span className="text-muted-foreground font-normal">(optional)</span>
            </Label>
            <Input
              id="scheduled-time"
              placeholder="e.g. 10:00–12:00"
              value={scheduledTime}
              onChange={(e) => setScheduledTime(e.target.value)}
              disabled={mutation.isPending}
            />
          </div>

          {/* Admin Remarks (optional) */}
          <div className="space-y-1.5">
            <Label htmlFor="admin-remarks" className="text-xs font-bold text-muted-foreground uppercase">
              Remarks <span className="text-muted-foreground font-normal">(optional)</span>
            </Label>
            <textarea
              id="admin-remarks"
              rows={2}
              placeholder="Any notes for the worker or student…"
              value={adminRemarks}
              onChange={(e) => setAdminRemarks(e.target.value)}
              disabled={mutation.isPending}
              className="flex w-full rounded-md border border-input bg-card px-3 py-2 text-sm shadow-xs placeholder:text-muted-foreground focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring disabled:opacity-50 text-foreground"
            />
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-2 mt-6">
          <Button variant="outline" size="sm" onClick={onClose} disabled={mutation.isPending} className="text-xs">
            Cancel
          </Button>
          <Button size="sm" onClick={handleSubmit} disabled={mutation.isPending} className="text-xs gap-1.5">
            {mutation.isPending && <Loader2 className="h-3 w-3 animate-spin" />}
            Schedule Visit
          </Button>
        </div>
      </div>
    </div>
  );
}
