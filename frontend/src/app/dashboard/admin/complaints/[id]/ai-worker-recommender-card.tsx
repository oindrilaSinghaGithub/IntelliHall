"use client";

import { useState, useEffect } from "react";
import { Wrench, UserCheck, Star, Sparkles, RefreshCw, Loader2, CheckCircle2, AlertTriangle, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { useWorkers } from "@/hooks/use-workers";

import { useUpdateComplaintFields } from "@/hooks/use-complaints";
import type { Complaint } from "@/types/complaint";

interface AiWorkerRecommenderCardProps {
  complaint: Complaint;
}

export function AiWorkerRecommenderCard({ complaint }: AiWorkerRecommenderCardProps) {
  // Fetch all workers in the hall (up to 100 for dropdown selection)
  const { data: staffData, isLoading: isStaffLoading } = useWorkers({ page: 1, page_size: 100 });
  const workersList = staffData?.items || [];

  const updateFieldsMutation = useUpdateComplaintFields(complaint.id);

  // Selected worker ID state
  const [selectedWorkerId, setSelectedWorkerId] = useState("");

  // Sync state with complaint updates
  useEffect(() => {
    const defaultId = complaint.assigned_worker_id || complaint.recommended_worker_id || "";
    setSelectedWorkerId(defaultId);
  }, [complaint.assigned_worker_id, complaint.recommended_worker_id]);

  // Find the recommended worker model in the fetched staff list
  const recommendedWorker = workersList.find((w) => w.id === complaint.recommended_worker_id);

  const handleAssign = () => {
    updateFieldsMutation.mutate({
      assigned_worker_id: selectedWorkerId || "", // empty string unassigns
    });
  };

  const handleForceRefresh = () => {
    updateFieldsMutation.mutate({
      force_recompute_recommendation: true,
    });
  };

  // Determine confidence color styling
  const getConfidenceBadgeColor = (confidence?: string | null) => {
    switch (confidence) {
      case "Very High":
        return "bg-emerald-500/10 text-emerald-500 border-emerald-500/20";
      case "High":
        return "bg-teal-500/10 text-teal-500 border-teal-500/20";
      case "Medium":
        return "bg-amber-500/10 text-amber-500 border-amber-500/20";
      case "Low":
      default:
        return "bg-rose-500/10 text-rose-500 border-rose-500/20";
    }
  };

  const isPending = updateFieldsMutation.isPending;

  return (
    <Card className="border border-border/50 bg-card overflow-hidden shadow-xs relative">
      {/* Decorative gradient header bar */}
      <div className="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r from-violet-600 via-indigo-600 to-sky-600" />
      
      <CardHeader className="pb-3 pt-5">
        <CardTitle className="text-sm font-bold flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-indigo-500 fill-indigo-500/10" />
            AI Worker Recommendation
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleForceRefresh}
            disabled={isPending || isStaffLoading}

            className="h-7 px-2 text-[10px] gap-1 hover:bg-muted font-semibold"
            title="Recalculate AI recommendation"
          >
            {isPending ? (
              <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />
            ) : (
              <RefreshCw className="h-3 w-3 text-muted-foreground" />
            )}
            Recalculate
          </Button>
        </CardTitle>
        <CardDescription className="text-[11px]">
          Matching technicians based on specialization, workload, availability, and rating.
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Recommendation Panel */}
        {isStaffLoading ? (
          <div className="flex h-24 items-center justify-center rounded-lg border border-border/30 bg-muted/20">
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
          </div>
        ) : complaint.recommended_worker_id && recommendedWorker ? (
          <div className="space-y-3.5">
            {/* Worker summary badge */}
            <div className="p-3.5 rounded-xl bg-indigo-500/[0.03] border border-indigo-500/15 space-y-2">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="text-sm font-bold text-foreground">{recommendedWorker.name}</h4>
                  <p className="text-[10px] text-muted-foreground capitalize mt-0.5">
                    {recommendedWorker.specialization.replace("_", " ")} • {recommendedWorker.experience_level}
                  </p>
                </div>
                
                <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold border ${getConfidenceBadgeColor(complaint.recommendation_confidence)}`}>
                  {complaint.recommendation_confidence} ({complaint.recommendation_score}%)
                </span>
              </div>

              {/* Bulleted justification list */}
              {complaint.recommendation_reason && (
                <ul className="space-y-1.5 pt-2 border-t border-border/40 text-[11px] text-muted-foreground">
                  {complaint.recommendation_reason.split("\n").map((bullet: string, idx: number) => {
                    const cleanText = bullet.replace(/^[✓⚠]\s*/, "");
                    const isWarning = bullet.startsWith("⚠");
                    return (
                      <li key={idx} className="flex items-start gap-1.5 leading-relaxed">
                        {isWarning ? (
                          <AlertTriangle className="h-3.5 w-3.5 text-amber-500 shrink-0 mt-0.5" />
                        ) : (
                          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0 mt-0.5" />
                        )}
                        <span className="text-foreground/80">{cleanText}</span>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          </div>
        ) : (
          /* Graceful Fallback / No workers found */
          <div className="p-3.5 rounded-xl bg-amber-500/[0.03] border border-amber-500/15 space-y-2 flex items-start gap-2.5">
            <AlertTriangle className="h-5 w-5 text-amber-500 shrink-0 mt-0.5" />
            <div>
              <h4 className="text-xs font-bold text-foreground">No Suitable Worker Found</h4>
              <p className="text-[11px] text-muted-foreground leading-relaxed mt-1 whitespace-pre-line">
                {complaint.recommendation_reason || "There are no workers matching the required specialization registered in this hall."}
              </p>
            </div>
          </div>
        )}

        {/* Assignment Action Selector */}
        <div className="space-y-3 pt-1">
          <div className="space-y-1.5">
            <Label htmlFor="staff-selector" className="text-[10px] font-bold text-muted-foreground uppercase flex items-center gap-1">
              <UserCheck className="h-3 w-3" /> Final Assignee Selection
            </Label>
            <select
              id="staff-selector"
              value={selectedWorkerId}
              onChange={(e) => setSelectedWorkerId(e.target.value)}
              disabled={isPending || isStaffLoading}
              className="flex h-9 w-full rounded-md border border-input bg-card px-3 py-1 text-sm shadow-xs text-foreground focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring"
            >
              <option value="">Unassigned / Clear Assignee</option>
              {workersList.map((w) => {
                const isRecommended = w.id === complaint.recommended_worker_id;
                const statusLabel = w.availability_status.replace("_", " ").toUpperCase();
                return (
                  <option key={w.id} value={w.id}>
                    {w.name} ({w.specialization.replace("_", " ").replace(/\b\w/g, c => c.toUpperCase())}) - {statusLabel} [Active: {w.active_jobs}] {isRecommended ? "⭐ (AI Pick)" : ""}
                  </option>
                );
              })}
            </select>
          </div>

          <Button
            size="sm"
            onClick={handleAssign}
            disabled={isPending || isStaffLoading || selectedWorkerId === (complaint.assigned_worker_id || "")}
            className="w-full text-xs font-semibold gap-1.5"
          >
            {isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            Confirm Assignment
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
