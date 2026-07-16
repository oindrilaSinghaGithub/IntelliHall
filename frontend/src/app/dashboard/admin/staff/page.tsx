"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Building2,
  LogOut,
  Users,
  Phone,
  Star,
  Trash2,
  Edit2,
  Plus,
  Wrench,
  ChevronLeft,
  ChevronRight,
  Loader2,
  X,
  Shield,
  Briefcase,
  AlertTriangle,
} from "lucide-react";

import { AuthGuard } from "@/components/shared/auth-guard";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/use-auth";
import { NotificationBell } from "@/components/shared/notification-bell";
import {
  useWorkers,
  useCreateWorker,
  useUpdateWorker,
  useDeleteWorker,
} from "@/hooks/use-workers";
import type {
  Worker,
  WorkerSpecialization,
  WorkerAvailability,
  WorkerExperienceLevel,
} from "@/types/worker";

const SPECIALIZATIONS: { value: WorkerSpecialization; label: string }[] = [
  { value: "electrician", label: "Electrician" },
  { value: "plumber", label: "Plumber" },
  { value: "carpenter", label: "Carpenter" },
  { value: "cleaning_staff", label: "Cleaning Staff" },
  { value: "network_staff", label: "Network Staff" },
  { value: "civil_maintenance", label: "Civil Maintenance" },
];

const AVAILABILITY_STATUSES: { value: WorkerAvailability; label: string }[] = [
  { value: "available", label: "Available" },
  { value: "busy", label: "Busy" },
  { value: "on_leave", label: "On Leave" },
];

const EXPERIENCE_LEVELS: { value: WorkerExperienceLevel; label: string }[] = [
  { value: "junior", label: "Junior" },
  { value: "intermediate", label: "Intermediate" },
  { value: "senior", label: "Senior" },
];

export default function HallStaffPage() {
  const { user, signOut } = useAuth();
  const [page, setPage] = useState(1);
  const pageSize = 10;

  // Fetch Workers
  const {
    data: paginatedData,
    isLoading,
    error,
    refetch,
  } = useWorkers({ page, page_size: pageSize });

  // Mutations
  const createMutation = useCreateWorker();
  const updateMutation = useUpdateWorker();
  const deleteMutation = useDeleteWorker();

  // Dialog states
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [selectedWorker, setSelectedWorker] = useState<Worker | null>(null);

  // Form states
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [specialization, setSpecialization] = useState<WorkerSpecialization>("electrician");
  const [availability, setAvailability] = useState<WorkerAvailability>("available");
  const [skillRating, setSkillRating] = useState(5.0);
  const [expYears, setExpYears] = useState(0);
  const [expLevel, setExpLevel] = useState<WorkerExperienceLevel>("intermediate");
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  const totalPages = paginatedData?.pages || 1;
  const workers = paginatedData?.items || [];

  const handlePrevPage = () => {
    setPage((old) => Math.max(old - 1, 1));
  };

  const handleNextPage = () => {
    if (page < totalPages) {
      setPage((old) => old + 1);
    }
  };

  const validate = () => {
    const errs: Record<string, string> = {};
    if (!name.trim()) errs.name = "Name is required.";
    if (!phone.trim()) errs.phone = "Phone number is required.";
    if (skillRating < 1.0 || skillRating > 5.0)
      errs.skillRating = "Skill rating must be between 1.0 and 5.0.";
    if (expYears < 0) errs.expYears = "Years of experience cannot be negative.";
    setFormErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const openAddDialog = () => {
    setName("");
    setPhone("");
    setSpecialization("electrician");
    setAvailability("available");
    setSkillRating(5.0);
    setExpYears(0);
    setExpLevel("intermediate");
    setFormErrors({});
    setIsAddOpen(true);
  };

  const handleCreate = () => {
    if (!validate()) return;
    createMutation.mutate(
      {
        name: name.trim(),
        phone: phone.trim(),
        specialization,
        availability_status: availability,
        skill_rating: skillRating,
        experience_years: expYears,
        experience_level: expLevel,
      },
      {
        onSuccess: () => {
          setIsAddOpen(false);
          refetch();
        },
      }
    );
  };

  const openEditDialog = (worker: Worker) => {
    setSelectedWorker(worker);
    setName(worker.name);
    setPhone(worker.phone);
    setSpecialization(worker.specialization);
    setAvailability(worker.availability_status);
    setSkillRating(worker.skill_rating);
    setExpYears(worker.experience_years);
    setExpLevel(worker.experience_level);
    setFormErrors({});
    setIsEditOpen(true);
  };

  const handleUpdate = () => {
    if (!selectedWorker || !validate()) return;
    updateMutation.mutate(
      {
        id: selectedWorker.id,
        data: {
          name: name.trim(),
          phone: phone.trim(),
          specialization,
          availability_status: availability,
          skill_rating: skillRating,
          experience_years: expYears,
          experience_level: expLevel,
        },
      },
      {
        onSuccess: () => {
          setIsEditOpen(false);
          refetch();
        },
      }
    );
  };

  const handleDelete = (id: string) => {
    if (confirm("Are you sure you want to remove this worker from the hall staff registry?")) {
      deleteMutation.mutate(id, {
        onSuccess: () => {
          refetch();
        },
      });
    }
  };

  const getAvailabilityBadge = (status: WorkerAvailability) => {
    switch (status) {
      case "available":
        return (
          <Badge className="bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 hover:bg-emerald-500/10">
            Available
          </Badge>
        );
      case "busy":
        return (
          <Badge className="bg-amber-500/10 text-amber-500 border border-amber-500/20 hover:bg-amber-500/10">
            Busy
          </Badge>
        );
      case "on_leave":
        return (
          <Badge className="bg-slate-500/10 text-slate-500 border border-slate-500/20 hover:bg-slate-500/10">
            On Leave
          </Badge>
        );
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-background">
      {/* Top nav */}
      <header className="sticky top-0 z-40 border-b border-border/60 bg-background/80 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Link href="/dashboard/admin" className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
              <Building2 className="h-4 w-4 text-primary" />
            </div>
            <span className="text-sm font-semibold tracking-tight">IntelliHall Admin</span>
          </Link>

          <div className="flex items-center gap-3">
            <div className="hidden text-right sm:block">
              <p className="text-sm font-medium">{user?.name}</p>
              <p className="text-xs text-muted-foreground">{user?.email}</p>
            </div>
            <Badge variant="default">Hall Admin</Badge>
            <NotificationBell />
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

      {/* Main Container */}
      <main className="flex-1">
        <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 space-y-6">
          
          {/* Header Actions */}
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="space-y-1">
              <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
                <Users className="h-6 w-6 text-primary" />
                Hall Staff Management
              </h1>
              <p className="text-sm text-muted-foreground">
                Manage maintenance workers, monitor workloads, and update availability status.
              </p>
            </div>
            <Button onClick={openAddDialog} className="gap-1.5 self-start sm:self-auto font-semibold">
              <Plus className="h-4 w-4" />
              Add Worker
            </Button>
          </div>

          {/* Error and Loading indicators */}
          {error ? (
            <Card className="border border-destructive/20 bg-destructive/10 p-6 text-center">
              <p className="text-sm font-medium text-destructive">
                Error loading staff registry: {error.message || "Please check connection and try again."}
              </p>
              <Button onClick={() => refetch()} variant="outline" size="sm" className="mt-4">
                Retry
              </Button>
            </Card>
          ) : isLoading ? (
            <div className="flex h-64 items-center justify-center rounded-2xl border border-border/50 bg-card">
              <div className="flex flex-col items-center gap-2">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <p className="text-xs text-muted-foreground">Fetching workers registry...</p>
              </div>
            </div>
          ) : workers.length === 0 ? (
            <div className="flex h-64 flex-col items-center justify-center rounded-2xl border border-dashed border-border/60 bg-card p-6 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <Wrench className="h-6 w-6" />
              </div>
              <h3 className="mt-4 text-sm font-semibold">No workers registered</h3>
              <p className="mt-1.5 text-xs text-muted-foreground max-w-sm">
                Add workers to your hall staff registry so that the AI recommender can match them to complaints.
              </p>
              <Button onClick={openAddDialog} size="sm" variant="outline" className="mt-4 gap-1">
                <Plus className="h-3.5 w-3.5" /> Add First Worker
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Workers Grid Layout */}
              <div className="grid gap-4 md:grid-cols-2">
                {workers.map((worker) => (
                  <Card key={worker.id} className="border border-border/50 bg-card shadow-xs">
                    <CardContent className="p-5 flex flex-col justify-between h-full space-y-4">
                      
                      {/* Top Info */}
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex gap-3">
                          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
                            <Wrench className="h-5 w-5" />
                          </div>
                          <div>
                            <h3 className="text-sm font-bold text-foreground">{worker.name}</h3>
                            <p className="text-xs text-muted-foreground flex items-center gap-1.5 mt-0.5">
                              <Phone className="h-3 w-3" />
                              {worker.phone}
                            </p>
                          </div>
                        </div>
                        {getAvailabilityBadge(worker.availability_status)}
                      </div>

                      {/* Details Strip */}
                      <div className="grid grid-cols-2 gap-2 p-3 rounded-lg bg-muted/40 border border-border/40 text-xs text-muted-foreground">
                        <div>
                          <p className="font-bold text-[10px] uppercase tracking-wider text-muted-foreground/80">Specialization</p>
                          <p className="font-medium text-foreground mt-0.5">
                            {worker.specialization.replace("_", " ").replace(/\b\w/g, c => c.toUpperCase())}
                          </p>
                        </div>
                        <div>
                          <p className="font-bold text-[10px] uppercase tracking-wider text-muted-foreground/80">Active Workload</p>
                          <p className="font-semibold text-foreground mt-0.5 flex items-center gap-1.5">
                            <Briefcase className="h-3 w-3 text-muted-foreground" />
                            {worker.active_jobs} active {worker.active_jobs === 1 ? "job" : "jobs"}
                          </p>
                        </div>
                        <div>
                          <p className="font-bold text-[10px] uppercase tracking-wider text-muted-foreground/80">Experience</p>
                          <p className="font-medium text-foreground mt-0.5">
                            {worker.experience_years} years ({worker.experience_level.toUpperCase()})
                          </p>
                        </div>
                        <div>
                          <p className="font-bold text-[10px] uppercase tracking-wider text-muted-foreground/80">Skill Rating</p>
                          <p className="font-semibold text-foreground mt-0.5 flex items-center gap-1">
                            <Star className="h-3.5 w-3.5 fill-amber-500 text-amber-500 shrink-0" />
                            {worker.skill_rating.toFixed(1)} / 5.0
                          </p>
                        </div>
                      </div>

                      {/* Action buttons */}
                      <div className="flex items-center justify-end gap-2 border-t border-border/30 pt-3">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openEditDialog(worker)}
                          className="h-8 gap-1 text-xs"
                        >
                          <Edit2 className="h-3.5 w-3.5" />
                          Edit
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(worker.id)}
                          className="h-8 gap-1 text-xs text-destructive hover:bg-destructive/10 hover:text-destructive"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                          Delete
                        </Button>
                      </div>

                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Pagination controls */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between border-t border-border/50 pt-4">
                  <p className="text-xs text-muted-foreground">
                    Showing Page <span className="font-semibold">{page}</span> of{" "}
                    <span className="font-semibold">{totalPages}</span>
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handlePrevPage}
                      disabled={page === 1}
                      className="h-8 w-8 p-0"
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleNextPage}
                      disabled={page === totalPages}
                      className="h-8 w-8 p-0"
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </main>

      {/* ---------------------------------------------------------------------
          MODALS / DIALOGS (Created manually via overlays for design alignment)
         --------------------------------------------------------------------- */}

      {/* Add Worker Dialog */}
      {isAddOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-xs">
          <div className="relative w-full max-w-md rounded-xl border border-border/80 bg-card p-6 shadow-2xl animate-in fade-in-50 zoom-in-95 duration-200">
            <button
              onClick={() => setIsAddOpen(false)}
              className="absolute right-4 top-4 rounded-md opacity-70 transition-opacity hover:opacity-100 focus:outline-hidden"
            >
              <X className="h-4 w-4" />
            </button>

            <div className="mb-5">
              <h3 className="text-lg font-semibold leading-none tracking-tight flex items-center gap-2">
                <Wrench className="h-5 w-5 text-primary" />
                Add Maintenance Worker
              </h3>
              <p className="text-xs text-muted-foreground mt-1.5">
                Register a new worker to this residential hall.
              </p>
            </div>

            <div className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="add-name" className="text-xs font-bold text-muted-foreground uppercase">
                  Name <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="add-name"
                  placeholder="e.g. Ramesh Kumar"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
                {formErrors.name && <p className="text-xs text-destructive">{formErrors.name}</p>}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="add-phone" className="text-xs font-bold text-muted-foreground uppercase">
                  Phone Number <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="add-phone"
                  placeholder="e.g. +91 98765 43210"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                />
                {formErrors.phone && <p className="text-xs text-destructive">{formErrors.phone}</p>}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="add-spec" className="text-xs font-bold text-muted-foreground uppercase">
                    Specialization
                  </Label>
                  <select
                    id="add-spec"
                    value={specialization}
                    onChange={(e) => setSpecialization(e.target.value as WorkerSpecialization)}
                    className="flex h-9 w-full rounded-md border border-input bg-card px-3 py-1 text-sm shadow-xs text-foreground focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring"
                  >
                    {SPECIALIZATIONS.map((s) => (
                      <option key={s.value} value={s.value}>
                        {s.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="add-avail" className="text-xs font-bold text-muted-foreground uppercase">
                    Availability
                  </Label>
                  <select
                    id="add-avail"
                    value={availability}
                    onChange={(e) => setAvailability(e.target.value as WorkerAvailability)}
                    className="flex h-9 w-full rounded-md border border-input bg-card px-3 py-1 text-sm shadow-xs text-foreground focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring"
                  >
                    {AVAILABILITY_STATUSES.map((a) => (
                      <option key={a.value} value={a.value}>
                        {a.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="add-rating" className="text-xs font-bold text-muted-foreground uppercase">
                    Skill Rating (1-5)
                  </Label>
                  <Input
                    id="add-rating"
                    type="number"
                    step="0.1"
                    min="1"
                    max="5"
                    value={skillRating}
                    onChange={(e) => setSkillRating(parseFloat(e.target.value) || 5.0)}
                  />
                  {formErrors.skillRating && <p className="text-xs text-destructive">{formErrors.skillRating}</p>}
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="add-expyears" className="text-xs font-bold text-muted-foreground uppercase">
                    Experience Years
                  </Label>
                  <Input
                    id="add-expyears"
                    type="number"
                    min="0"
                    value={expYears}
                    onChange={(e) => setExpYears(parseInt(e.target.value) || 0)}
                  />
                  {formErrors.expYears && <p className="text-xs text-destructive">{formErrors.expYears}</p>}
                </div>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="add-explevel" className="text-xs font-bold text-muted-foreground uppercase">
                  Experience Level
                </Label>
                <select
                  id="add-explevel"
                  value={expLevel}
                  onChange={(e) => setExpLevel(e.target.value as WorkerExperienceLevel)}
                  className="flex h-9 w-full rounded-md border border-input bg-card px-3 py-1 text-sm shadow-xs text-foreground focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring"
                >
                  {EXPERIENCE_LEVELS.map((el) => (
                    <option key={el.value} value={el.value}>
                      {el.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 mt-6">
              <Button variant="outline" size="sm" onClick={() => setIsAddOpen(false)} className="text-xs">
                Cancel
              </Button>
              <Button size="sm" onClick={handleCreate} disabled={createMutation.isPending} className="text-xs gap-1.5">
                {createMutation.isPending && <Loader2 className="h-3 w-3 animate-spin" />}
                Add Worker
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Worker Dialog */}
      {isEditOpen && selectedWorker && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-xs">
          <div className="relative w-full max-w-md rounded-xl border border-border/80 bg-card p-6 shadow-2xl animate-in fade-in-50 zoom-in-95 duration-200">
            <button
              onClick={() => setIsEditOpen(false)}
              className="absolute right-4 top-4 rounded-md opacity-70 transition-opacity hover:opacity-100 focus:outline-hidden"
            >
              <X className="h-4 w-4" />
            </button>

            <div className="mb-5">
              <h3 className="text-lg font-semibold leading-none tracking-tight flex items-center gap-2">
                <Edit2 className="h-5 w-5 text-primary" />
                Edit Worker Details
              </h3>
              <p className="text-xs text-muted-foreground mt-1.5">
                Update attributes for {selectedWorker.name}.
              </p>
            </div>

            <div className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="edit-name" className="text-xs font-bold text-muted-foreground uppercase">
                  Name <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="edit-name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
                {formErrors.name && <p className="text-xs text-destructive">{formErrors.name}</p>}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="edit-phone" className="text-xs font-bold text-muted-foreground uppercase">
                  Phone Number <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="edit-phone"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                />
                {formErrors.phone && <p className="text-xs text-destructive">{formErrors.phone}</p>}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="edit-spec" className="text-xs font-bold text-muted-foreground uppercase">
                    Specialization
                  </Label>
                  <select
                    id="edit-spec"
                    value={specialization}
                    onChange={(e) => setSpecialization(e.target.value as WorkerSpecialization)}
                    className="flex h-9 w-full rounded-md border border-input bg-card px-3 py-1 text-sm shadow-xs text-foreground focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring"
                  >
                    {SPECIALIZATIONS.map((s) => (
                      <option key={s.value} value={s.value}>
                        {s.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="edit-avail" className="text-xs font-bold text-muted-foreground uppercase">
                    Availability
                  </Label>
                  <select
                    id="edit-avail"
                    value={availability}
                    onChange={(e) => setAvailability(e.target.value as WorkerAvailability)}
                    className="flex h-9 w-full rounded-md border border-input bg-card px-3 py-1 text-sm shadow-xs text-foreground focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring"
                  >
                    {AVAILABILITY_STATUSES.map((a) => (
                      <option key={a.value} value={a.value}>
                        {a.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="edit-rating" className="text-xs font-bold text-muted-foreground uppercase">
                    Skill Rating (1-5)
                  </Label>
                  <Input
                    id="edit-rating"
                    type="number"
                    step="0.1"
                    min="1"
                    max="5"
                    value={skillRating}
                    onChange={(e) => setSkillRating(parseFloat(e.target.value) || 5.0)}
                  />
                  {formErrors.skillRating && <p className="text-xs text-destructive">{formErrors.skillRating}</p>}
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="edit-expyears" className="text-xs font-bold text-muted-foreground uppercase">
                    Experience Years
                  </Label>
                  <Input
                    id="edit-expyears"
                    type="number"
                    min="0"
                    value={expYears}
                    onChange={(e) => setExpYears(parseInt(e.target.value) || 0)}
                  />
                  {formErrors.expYears && <p className="text-xs text-destructive">{formErrors.expYears}</p>}
                </div>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="edit-explevel" className="text-xs font-bold text-muted-foreground uppercase">
                  Experience Level
                </Label>
                <select
                  id="edit-explevel"
                  value={expLevel}
                  onChange={(e) => setExpLevel(e.target.value as WorkerExperienceLevel)}
                  className="flex h-9 w-full rounded-md border border-input bg-card px-3 py-1 text-sm shadow-xs text-foreground focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring"
                >
                  {EXPERIENCE_LEVELS.map((el) => (
                    <option key={el.value} value={el.value}>
                      {el.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 mt-6">
              <Button variant="outline" size="sm" onClick={() => setIsEditOpen(false)} className="text-xs">
                Cancel
              </Button>
              <Button size="sm" onClick={handleUpdate} disabled={updateMutation.isPending} className="text-xs gap-1.5">
                {updateMutation.isPending && <Loader2 className="h-3 w-3 animate-spin" />}
                Save Changes
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
