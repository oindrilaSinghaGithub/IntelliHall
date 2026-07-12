"use client";

import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  Building2,
  LogOut,
  User,
  CheckCircle2,
  Clock,
  XCircle,
  AlertTriangle,
  Loader2,
} from "lucide-react";

import { AuthGuard } from "@/components/shared/auth-guard";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/hooks/use-auth";
import { useHalls } from "@/hooks/use-halls";
import { useUpdateMyHall } from "@/hooks/use-verification";
import { updateHallSchema, type UpdateHallFormValues } from "@/lib/schemas";

// ---------------------------------------------------------------------------
// Verification status display helper
// ---------------------------------------------------------------------------

function VerificationStatusBadge({ status }: { status: string | undefined }) {
  if (status === "approved") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">
        <CheckCircle2 className="h-3.5 w-3.5" />
        Hall Verified
      </span>
    );
  }
  if (status === "pending") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
        <Clock className="h-3.5 w-3.5" />
        Pending Verification
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-destructive/10 px-3 py-1 text-xs font-semibold text-destructive">
      <XCircle className="h-3.5 w-3.5" />
      Verification Rejected
    </span>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function ProfilePage() {
  const { user, signOut } = useAuth();
  const { data: halls, isLoading: isHallsLoading } = useHalls();
  const updateHallMutation = useUpdateMyHall();
  const [showHallWarning, setShowHallWarning] = useState(false);
  const [pendingValues, setPendingValues] = useState<UpdateHallFormValues | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isDirty },
  } = useForm<UpdateHallFormValues>({
    resolver: zodResolver(updateHallSchema),
    defaultValues: {
      hall_id: user?.hall_id ?? "",
      room_number: user?.room_number ?? "",
    },
  });

  const selectedHallId = watch("hall_id");
  const isChangingHall = selectedHallId !== user?.hall_id;

  function onSubmit(values: UpdateHallFormValues) {
    if (isChangingHall && !showHallWarning) {
      setPendingValues(values);
      setShowHallWarning(true);
      return;
    }
    const payload = pendingValues ?? values;
    setShowHallWarning(false);
    setPendingValues(null);
    updateHallMutation.mutate({
      hall_id: payload.hall_id,
      room_number: payload.room_number || null,
    });
  }

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
          <div className="mx-auto max-w-2xl px-4 py-10 sm:px-6">
            <div className="mb-8">
              <h1 className="text-2xl font-bold flex items-center gap-2">
                <User className="h-6 w-6 text-primary" />
                My Profile
              </h1>
              <p className="mt-1 text-sm text-muted-foreground">
                View your account details and manage your hall affiliation.
              </p>
            </div>

            {/* Account information */}
            <Card className="mb-6 border border-border/50">
              <CardHeader className="pb-4">
                <CardTitle className="text-base">Account Information</CardTitle>
                <CardDescription>Your personal details. Contact support to update name or email.</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4 sm:grid-cols-2">
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Full Name</p>
                  <p className="text-sm font-medium">{user?.name}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Email</p>
                  <p className="text-sm font-medium">{user?.email}</p>
                </div>
                {user?.roll_number && (
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">Roll Number</p>
                    <p className="text-sm font-medium">{user.roll_number}</p>
                  </div>
                )}
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Role</p>
                  <p className="text-sm font-medium capitalize">{user?.role?.replace("_", " ")}</p>
                </div>
              </CardContent>
            </Card>

            {/* Hall verification status */}
            {user?.role === "student" && (
              <Card className="mb-6 border border-border/50">
                <CardHeader className="pb-4">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">Hall Verification Status</CardTitle>
                    <VerificationStatusBadge status={user?.hall_verification_status} />
                  </div>
                </CardHeader>
                <CardContent>
                  {user?.hall_verification_status === "approved" && (
                    <p className="text-sm text-emerald-600 dark:text-emerald-400">
                      ✓ Your hall affiliation has been verified. You can submit complaints.
                    </p>
                  )}
                  {user?.hall_verification_status === "pending" && (
                    <p className="text-sm text-amber-600 dark:text-amber-500">
                      Your request is awaiting review by the Hall Office. Complaint submission
                      will be enabled once approved.
                    </p>
                  )}
                  {user?.hall_verification_status === "rejected" && (
                    <div>
                      <p className="text-sm text-destructive font-medium">
                        Your hall affiliation request was rejected.
                      </p>
                      {user.hall_rejection_reason && (
                        <p className="mt-1 text-xs text-muted-foreground">
                          Reason: {user.hall_rejection_reason}
                        </p>
                      )}
                      <p className="mt-2 text-xs text-muted-foreground">
                        Update your hall below and save to re-submit for verification.
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Hall affiliation edit */}
            {user?.role === "student" && (
              <Card className="border border-border/50">
                <CardHeader className="pb-4">
                  <CardTitle className="text-base">Hall Affiliation</CardTitle>
                  <CardDescription>
                    Update your hall or room number. Changing your hall will reset your
                    verification and require re-approval from the new Hall Admin.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
                    {/* Hall Warning */}
                    {showHallWarning && (
                      <div className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 dark:border-amber-800/40 dark:bg-amber-900/20">
                        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" />
                        <div className="flex-1 text-xs text-amber-700 dark:text-amber-400">
                          <p className="font-semibold mb-1">Changing hall will reset your verification.</p>
                          <p>You will not be able to submit new complaints until the new Hall Admin approves your request. Existing complaints will remain unaffected.</p>
                          <div className="mt-3 flex gap-2">
                            <Button
                              type="button"
                              size="sm"
                              onClick={() => handleSubmit(onSubmit)()}
                              disabled={updateHallMutation.isPending}
                              className="h-7 text-xs"
                            >
                              {updateHallMutation.isPending && <Loader2 className="mr-1.5 h-3 w-3 animate-spin" />}
                              Confirm Change
                            </Button>
                            <Button
                              type="button"
                              size="sm"
                              variant="ghost"
                              onClick={() => { setShowHallWarning(false); setPendingValues(null); }}
                              className="h-7 text-xs"
                            >
                              Cancel
                            </Button>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Hall dropdown */}
                    <div className="space-y-2">
                      <Label htmlFor="hall_id">Hall of Residence</Label>
                      {isHallsLoading ? (
                        <div className="flex items-center gap-2 text-xs text-muted-foreground bg-muted/30 border border-border/40 rounded-lg p-2.5">
                          <Loader2 className="h-3 w-3 animate-spin text-primary" />
                          Loading halls...
                        </div>
                      ) : (
                        <select
                          id="hall_id"
                          className={`flex h-9 w-full rounded-md border border-input bg-card px-3 py-1 text-sm shadow-xs transition-colors focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 text-foreground ${
                            errors.hall_id ? "border-destructive focus-visible:ring-destructive" : ""
                          }`}
                          {...register("hall_id")}
                          disabled={updateHallMutation.isPending}
                        >
                          <option value="">Select hall of residence...</option>
                          {halls?.map((h) => (
                            <option key={h.id} value={h.id}>
                              {h.name}
                            </option>
                          ))}
                        </select>
                      )}
                      {errors.hall_id && (
                        <p className="text-xs text-destructive">{errors.hall_id.message}</p>
                      )}
                    </div>

                    {/* Room number */}
                    <div className="space-y-2">
                      <Label htmlFor="room_number">
                        Room Number{" "}
                        <span className="text-muted-foreground font-normal">(optional)</span>
                      </Label>
                      <Input
                        id="room_number"
                        placeholder="e.g. B-302"
                        {...register("room_number")}
                        disabled={updateHallMutation.isPending}
                        className={errors.room_number ? "border-destructive focus-visible:ring-destructive" : ""}
                      />
                      {errors.room_number && (
                        <p className="text-xs text-destructive">{errors.room_number.message}</p>
                      )}
                    </div>

                    <Separator />

                    <div className="flex gap-3">
                      <Button
                        type="submit"
                        disabled={!isDirty || updateHallMutation.isPending}
                        className="gap-2"
                      >
                        {updateHallMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                        {isChangingHall ? "Change Hall" : "Save Changes"}
                      </Button>
                      <Button variant="outline" type="button" asChild>
                        <Link href="/dashboard">Cancel</Link>
                      </Button>
                    </div>
                  </form>
                </CardContent>
              </Card>
            )}
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
