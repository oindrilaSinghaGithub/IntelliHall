"use client";

import { useState } from "react";
import { Wrench, UserCheck, Clock, Save, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useUpdateComplaintFields } from "@/hooks/use-complaints";
import type { MaintenanceType } from "@/types/complaint";

// List of allowed maintenance worker classifications
const MAINTENANCE_TYPES: MaintenanceType[] = [
  "electrician",
  "plumber",
  "carpenter",
  "civil",
  "network",
  "housekeeping",
  "other",
];

interface AssignmentPanelProps {
  complaintId: string;
  initialMaintenanceType: MaintenanceType | null;
  initialAssignee: string | null;
  initialVisitTime: string | null;
}

// Convert ISO string (e.g. 2026-07-09T13:42:00Z) to YYYY-MM-DDTHH:MM for datetime-local
function toLocalDatetimeString(isoString?: string | null): string {
  if (!isoString) return "";
  const d = new Date(isoString);
  if (isNaN(d.getTime())) return "";
  const pad = (n: number) => n.toString().padStart(2, "0");
  const year = d.getFullYear();
  const month = pad(d.getMonth() + 1);
  const day = pad(d.getDate());
  const hours = pad(d.getHours());
  const minutes = pad(d.getMinutes());
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

export function AssignmentPanel({
  complaintId,
  initialMaintenanceType,
  initialAssignee,
  initialVisitTime,
}: AssignmentPanelProps) {
  const [maintenanceType, setMaintenanceType] = useState<string>(initialMaintenanceType || "");
  const [assignee, setAssignee] = useState<string>(initialAssignee || "");
  const [visitTime, setVisitTime] = useState<string>(toLocalDatetimeString(initialVisitTime));

  const updateFieldsMutation = useUpdateComplaintFields(complaintId);

  const handleSave = () => {
    const payload: Record<string, string | number | boolean | null | undefined> = {
      maintenance_type: maintenanceType || null,
      current_assignee: assignee.trim() ? assignee : null,
      preferred_visit_time: visitTime ? new Date(visitTime).toISOString() : null,
    };

    updateFieldsMutation.mutate(payload);
  };

  const hasChanges =
    maintenanceType !== (initialMaintenanceType || "") ||
    assignee !== (initialAssignee || "") ||
    visitTime !== toLocalDatetimeString(initialVisitTime);

  return (
    <Card className="border border-border/50 bg-card">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-bold flex items-center gap-2">
          <Wrench className="h-4 w-4 text-primary" />
          Maintenance Assignment Panel
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Classification */}
        <div className="space-y-1.5">
          <Label htmlFor="maintenance_type" className="text-[10px] font-bold text-muted-foreground uppercase flex items-center gap-1">
            <Wrench className="h-3 w-3" /> Worker Classification
          </Label>
          <select
            id="maintenance_type"
            value={maintenanceType}
            onChange={(e) => setMaintenanceType(e.target.value)}
            disabled={updateFieldsMutation.isPending}
            className="flex h-9 w-full rounded-md border border-input bg-card px-3 py-1 text-sm shadow-xs text-foreground focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring"
          >
            <option value="">Select worker type...</option>
            {MAINTENANCE_TYPES.map((t) => (
              <option key={t} value={t}>
                {t.toUpperCase()}
              </option>
            ))}
          </select>
        </div>

        {/* Technician Name */}
        <div className="space-y-1.5">
          <Label htmlFor="assignee" className="text-[10px] font-bold text-muted-foreground uppercase flex items-center gap-1">
            <UserCheck className="h-3 w-3" /> Assigned Worker Name
          </Label>
          <Input
            id="assignee"
            type="text"
            placeholder="Enter technician name..."
            value={assignee}
            onChange={(e) => setAssignee(e.target.value)}
            disabled={updateFieldsMutation.isPending}
          />
        </div>

        {/* Scheduled Time */}
        <div className="space-y-1.5">
          <Label htmlFor="visit_time" className="text-[10px] font-bold text-muted-foreground uppercase flex items-center gap-1">
            <Clock className="h-3 w-3" /> Scheduled Visit Time
          </Label>
          <input
            id="visit_time"
            type="datetime-local"
            value={visitTime}
            onChange={(e) => setVisitTime(e.target.value)}
            disabled={updateFieldsMutation.isPending}
            className="flex h-9 w-full rounded-md border border-input bg-card px-3 py-1 text-sm shadow-xs text-foreground focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring"
          />
        </div>

        {/* Action Button */}
        <div className="pt-2">
          <Button
            size="sm"
            onClick={handleSave}
            disabled={!hasChanges || updateFieldsMutation.isPending}
            className="w-full text-xs gap-1.5"
          >
            {updateFieldsMutation.isPending ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Save className="h-3.5 w-3.5" />
            )}
            Save Assignment Details
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
