"use client";

import Link from "next/link";
import { ArrowLeft, Building2, ClipboardList, LogOut } from "lucide-react";

import { AuthGuard } from "@/components/shared/auth-guard";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/hooks/use-auth";
import { useCreateComplaint } from "@/hooks/use-complaints";
import { ComplaintForm } from "@/components/shared/complaint-form";
import type { ComplaintFormValues } from "@/lib/schemas";

export default function RaiseComplaintPage() {
  const { user, signOut } = useAuth();
  const createComplaintMutation = useCreateComplaint();

  const handleFormSubmit = (values: ComplaintFormValues) => {
    // Standardize request payload matching FastAPI constraints
    // Clean empty values to null so the backend handles optional keys correctly.
    const payload = {
      title: values.title,
      description: values.description,
      complaint_type: values.complaint_type,
      category: values.category,
      priority: values.priority,
      room_number: values.complaint_type === "personal" ? (values.room_number || null) : null,
      block: values.complaint_type === "common_area" ? (values.block || null) : null,
      floor: values.complaint_type === "common_area" ? (values.floor || null) : null,
      common_area: values.complaint_type === "common_area" ? (values.common_area || null) : null,
      qr_location_id: values.complaint_type === "common_area" ? (values.qr_location_id || null) : null,
      preferred_visit_time: values.preferred_visit_time || null,
    };

    createComplaintMutation.mutate(payload);
  };

  return (
    <AuthGuard>
      <div className="flex min-h-screen flex-col bg-background">
        {/* Top nav */}
        <header className="sticky top-0 z-40 border-b border-border/60 bg-background/80 backdrop-blur-xl">
          <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
            <Link href="/dashboard" className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
                <Building2 className="h-4 w-4 text-primary" />
              </div>
              <span className="text-sm font-semibold tracking-tight">IntelliHall</span>
            </Link>

            <div className="flex items-center gap-3">
              <div className="hidden text-right sm:block">
                <p className="text-sm font-medium">{user?.name}</p>
                <p className="text-xs text-muted-foreground">{user?.email}</p>
              </div>
              <Badge variant={user?.role === "hall_admin" ? "default" : "secondary"}>
                {user?.role === "hall_admin" ? "Hall Admin" : "Student"}
              </Badge>
              <Button
                variant="ghost"
                size="sm"
                onClick={signOut}
                className="gap-2 text-muted-foreground hover:text-foreground"
              >
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">Sign out</span>
              </Button>
            </div>
          </div>
        </header>

        {/* Main content */}
        <main className="flex-1">
          <div className="mx-auto max-w-2xl px-4 py-8 sm:px-6">
            {/* Header section */}
            <div className="space-y-1 mb-8">
              <Link
                href="/dashboard/complaints"
                className="inline-flex items-center text-xs font-medium text-muted-foreground hover:text-primary gap-1 mb-2 transition-colors"
              >
                <ArrowLeft className="h-3 w-3" />
                Back to My Complaints
              </Link>
              <h1 className="text-2xl font-bold flex items-center gap-2">
                <ClipboardList className="h-6 w-6 text-primary" />
                Raise a Complaint
              </h1>
              <p className="text-sm text-muted-foreground">
                Describe the problem and specify the location. Our maintenance team will look into it.
              </p>
            </div>

            {/* Form */}
            <ComplaintForm
              onSubmit={handleFormSubmit}
              isLoading={createComplaintMutation.isPending}
            />
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
