"use client";

import { useState } from "react";
import { X, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";

interface RemarksDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (remarks: string) => void;
  title: string;
  description: string;
  confirmText?: string;
  isLoading?: boolean;
}

export function RemarksDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  description,
  confirmText = "Confirm",
  isLoading = false,
}: RemarksDialogProps) {
  const [remarks, setRemarks] = useState("");

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-xs">
      {/* Modal Card */}
      <div className="relative w-full max-w-md rounded-xl border border-border/80 bg-card p-6 shadow-2xl animate-in fade-in-50 zoom-in-95 duration-200">
        {/* Close Button */}
        <button
          onClick={onClose}
          disabled={isLoading}
          className="absolute right-4 top-4 rounded-md opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-hidden disabled:pointer-events-none"
        >
          <X className="h-4 w-4" />
          <span className="sr-only">Close</span>
        </button>

        {/* Content Header */}
        <div className="space-y-1.5 text-left mb-4">
          <h3 className="text-lg font-semibold leading-none tracking-tight text-foreground">
            {title}
          </h3>
          <p className="text-xs text-muted-foreground">
            {description}
          </p>
        </div>

        {/* Input Textarea */}
        <div className="space-y-2 mb-6">
          <Label htmlFor="remarks" className="text-xs font-bold text-muted-foreground uppercase">
            Remarks / Comments (Optional)
          </Label>
          <textarea
            id="remarks"
            rows={3}
            placeholder="Type any notes, visits log details, or remarks..."
            value={remarks}
            onChange={(e) => setRemarks(e.target.value)}
            disabled={isLoading}
            className="flex w-full rounded-md border border-input bg-card px-3 py-2 text-sm shadow-xs transition-colors placeholder:text-muted-foreground focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 text-foreground"
          />
        </div>

        {/* Buttons Action Bar */}
        <div className="flex items-center justify-end gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onClose}
            disabled={isLoading}
            className="text-xs"
          >
            Cancel
          </Button>
          <Button
            size="sm"
            onClick={() => onConfirm(remarks)}
            disabled={isLoading}
            className="text-xs gap-1.5"
          >
            {isLoading && <Loader2 className="h-3 w-3 animate-spin" />}
            {confirmText}
          </Button>
        </div>
      </div>
    </div>
  );
}
