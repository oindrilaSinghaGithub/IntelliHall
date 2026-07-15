"use client";

import { Sparkles, AlertTriangle, TrendingUp } from "lucide-react";
import type { ComplaintPriority } from "@/types/complaint";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface AiPriorityBadgeProps {
  /** The student's manually selected priority */
  studentPriority: ComplaintPriority;
  /** AI-predicted priority (null = AI not run yet / pre-feature complaints) */
  predictedPriority?: ComplaintPriority | null;
  /** Confidence score 0.0 – 1.0 */
  aiConfidence?: number | null;
  /** Display mode: 'card' for sidebar panels, 'inline' for header areas */
  variant?: "card" | "inline";
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const PRIORITY_LABEL: Record<ComplaintPriority, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
  critical: "Critical",
};

const PRIORITY_COLORS: Record<ComplaintPriority, string> = {
  low: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20",
  medium: "bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 border-yellow-500/20",
  high: "bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/20",
  critical: "bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20",
};

/** Higher priority wins for display ordering */
const PRIORITY_RANK: Record<ComplaintPriority, number> = {
  low: 0,
  medium: 1,
  high: 2,
  critical: 3,
};

function ConfidenceBar({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100);
  const barColor =
    pct >= 80
      ? "bg-emerald-500"
      : pct >= 60
      ? "bg-yellow-500"
      : "bg-orange-500";

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-[10px] font-bold tabular-nums text-muted-foreground">
        {pct}%
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// AiPriorityBadge
// ---------------------------------------------------------------------------

/**
 * Displays the AI-predicted priority alongside a confidence bar.
 * Shows a mismatch warning when the AI recommendation differs from the
 * student's manually selected priority.
 *
 * Renders nothing when `predictedPriority` is null/undefined (backwards
 * compatible with complaints created before the AI feature was added).
 */
export function AiPriorityBadge({
  studentPriority,
  predictedPriority,
  aiConfidence,
  variant = "card",
}: AiPriorityBadgeProps) {
  // Don't render for old complaints that have no AI data
  if (!predictedPriority) return null;

  const isMismatch = predictedPriority !== studentPriority;
  const confidence = aiConfidence ?? 0;
  const aiRecommendsHigher =
    isMismatch && PRIORITY_RANK[predictedPriority] > PRIORITY_RANK[studentPriority];

  if (variant === "inline") {
    // -----------------------------------------------------------------------
    // Inline variant — compact, used next to the student-selected priority badge
    // -----------------------------------------------------------------------
    return (
      <div className="flex flex-wrap items-center gap-2">
        {/* AI badge */}
        <span
          className={`inline-flex items-center gap-1 font-semibold px-2.5 py-0.5 rounded text-xs border uppercase ${PRIORITY_COLORS[predictedPriority]}`}
          title={`AI confidence: ${Math.round(confidence * 100)}%`}
        >
          <Sparkles className="h-3 w-3 shrink-0" />
          AI: {PRIORITY_LABEL[predictedPriority]}
        </span>

        {/* Mismatch warning */}
        {isMismatch && aiRecommendsHigher && (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 animate-pulse">
            <AlertTriangle className="h-3 w-3 shrink-0" />
            AI recommends {PRIORITY_LABEL[predictedPriority]} Priority
          </span>
        )}
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Card variant — full panel, used in sidebars
  // -------------------------------------------------------------------------
  return (
    <div
      className={`rounded-xl border p-4 space-y-3 ${
        isMismatch && aiRecommendsHigher
          ? "border-amber-500/30 bg-amber-500/5"
          : "border-border/50 bg-card"
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-violet-500/10">
            <Sparkles className="h-3.5 w-3.5 text-violet-500" />
          </div>
          <span className="text-xs font-bold uppercase tracking-wider text-foreground/80">
            AI Priority Analysis
          </span>
        </div>
        {isMismatch && aiRecommendsHigher && (
          <span className="flex items-center gap-1 text-[9px] font-bold uppercase px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
            <TrendingUp className="h-2.5 w-2.5" />
            Mismatch
          </span>
        )}
      </div>

      {/* Predicted priority badge */}
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
          Suggested Priority
        </span>
        <span
          className={`inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded border uppercase ${PRIORITY_COLORS[predictedPriority]}`}
        >
          <Sparkles className="h-2.5 w-2.5" />
          {PRIORITY_LABEL[predictedPriority]}
        </span>
      </div>

      {/* Student priority for comparison */}
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
          Student Selected
        </span>
        <span
          className={`inline-flex items-center text-[10px] font-bold px-2 py-0.5 rounded border uppercase ${PRIORITY_COLORS[studentPriority]}`}
        >
          {PRIORITY_LABEL[studentPriority]}
        </span>
      </div>

      {/* Confidence bar */}
      <div className="space-y-1">
        <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
          Confidence
        </span>
        <ConfidenceBar confidence={confidence} />
      </div>

      {/* Mismatch warning message */}
      {isMismatch && aiRecommendsHigher && (
        <div className="flex items-start gap-2 p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20">
          <AlertTriangle className="h-3.5 w-3.5 text-amber-500 shrink-0 mt-0.5" />
          <p className="text-[10px] leading-relaxed text-amber-700 dark:text-amber-400 font-medium">
            The AI analysis suggests this complaint may warrant a{" "}
            <strong>{PRIORITY_LABEL[predictedPriority]}</strong> priority based
            on keywords in the description. Please review before proceeding.
          </p>
        </div>
      )}
    </div>
  );
}
