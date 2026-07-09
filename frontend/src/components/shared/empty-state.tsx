import { ClipboardX } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";

interface EmptyStateProps {
  title?: string;
  description?: string;
  actionLabel?: string;
  actionHref?: string;
}

export function EmptyState({
  title = "No complaints found",
  description = "You haven't raised any maintenance complaints yet.",
  actionLabel = "Raise a Complaint",
  actionHref = "/dashboard/complaints/new",
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-border/80 bg-card p-12 text-center shadow-xs">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-muted/60 text-muted-foreground mb-4">
        <ClipboardX className="h-7 w-7 text-muted-foreground/80" />
      </div>
      <h3 className="text-lg font-semibold tracking-tight">{title}</h3>
      <p className="mt-1.5 text-sm text-muted-foreground max-w-sm mb-6">
        {description}
      </p>
      {actionHref && actionLabel && (
        <Button asChild>
          <Link href={actionHref}>{actionLabel}</Link>
        </Button>
      )}
    </div>
  );
}
