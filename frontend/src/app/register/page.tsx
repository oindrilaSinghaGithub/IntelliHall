"use client";

import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Building2, Eye, EyeOff, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/use-auth";
import { useHalls } from "@/hooks/use-halls";
import { registerSchema, type RegisterFormValues } from "@/lib/schemas";

export default function RegisterPage() {
  const { signUp, extractApiError } = useAuth();
  const { data: halls, isLoading: isHallsLoading, error: hallsError } = useHalls();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    setError,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      name: "",
      email: "",
      password: "",
      confirmPassword: "",
      role: "student",
      hall_id: "",
    },
  });

  const selectedRole = watch("role");

  async function onSubmit(values: RegisterFormValues) {
    setIsLoading(true);
    try {
      // Strip confirmPassword — not part of the backend schema
      const { confirmPassword, ...payload } = values;
      void confirmPassword; // intentionally excluded from the API call
      await signUp(payload);
    } catch (err) {
      const message = extractApiError(err);
      if (message.toLowerCase().includes("email")) {
        setError("email", { message });
      } else {
        toast.error(message);
      }
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-background via-background to-primary/5 px-4 py-12">
      {/* Background decoration */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -left-40 -top-40 h-80 w-80 rounded-full bg-primary/10 blur-3xl" />
        <div className="absolute -bottom-40 -right-40 h-80 w-80 rounded-full bg-primary/10 blur-3xl" />
      </div>

      <div className="relative w-full max-w-md">
        {/* Logo */}
        <div className="mb-8 flex flex-col items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 ring-1 ring-primary/20">
            <Building2 className="h-6 w-6 text-primary" />
          </div>
          <div className="text-center">
            <h1 className="text-2xl font-bold tracking-tight">IntelliHall</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Create your account to get started
            </p>
          </div>
        </div>

        <Card className="border-border/50 shadow-2xl shadow-primary/5">
          <CardHeader className="space-y-1 pb-6">
            <CardTitle className="text-xl">Create an account</CardTitle>
            <CardDescription>
              Fill in your details to register
            </CardDescription>
          </CardHeader>

          <form onSubmit={handleSubmit(onSubmit)} noValidate>
            <CardContent className="space-y-4">
              {/* Full Name */}
              <div className="space-y-2">
                <Label htmlFor="name">Full name</Label>
                <Input
                  id="name"
                  type="text"
                  placeholder="Aarav Sharma"
                  autoComplete="name"
                  aria-invalid={!!errors.name}
                  {...register("name")}
                  className={errors.name ? "border-destructive focus-visible:ring-destructive" : ""}
                />
                {errors.name && (
                  <p className="text-xs text-destructive">{errors.name.message}</p>
                )}
              </div>

              {/* Email */}
              <div className="space-y-2">
                <Label htmlFor="email">Email address</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@iitgn.ac.in"
                  autoComplete="email"
                  aria-invalid={!!errors.email}
                  {...register("email")}
                  className={errors.email ? "border-destructive focus-visible:ring-destructive" : ""}
                />
                {errors.email && (
                  <p className="text-xs text-destructive">{errors.email.message}</p>
                )}
              </div>

              {/* Role selector */}
              <div className="space-y-2">
                <Label>I am a</Label>
                <div className="grid grid-cols-2 gap-2">
                  {(["student", "hall_admin"] as const).map((role) => (
                    <button
                      key={role}
                      type="button"
                      onClick={() => {
                        setValue("role", role);
                      }}
                      className={`flex items-center justify-center gap-2 rounded-lg border px-3 py-2.5 text-sm font-medium transition-all ${
                        selectedRole === role
                          ? "border-primary bg-primary/10 text-primary"
                          : "border-border bg-background text-muted-foreground hover:border-primary/50 hover:text-foreground"
                      }`}
                    >
                      {role === "student" ? "🎓 Student" : "🏛️ Hall Admin"}
                    </button>
                  ))}
                </div>
                {selectedRole === "hall_admin" && (
                  <p className="flex items-center gap-1.5 text-xs text-amber-500 dark:text-amber-400">
                    <span>⚠</span>
                    Hall admin accounts require approval from the warden.
                  </p>
                )}
              </div>

              {/* Hall Selector (Mandatory for both) */}
              <div className="space-y-2">
                <Label htmlFor="hall_id">Hall of Residence</Label>
                {isHallsLoading ? (
                  <div className="flex items-center gap-2 text-xs text-muted-foreground bg-muted/30 border border-border/40 rounded-lg p-2.5">
                    <Loader2 className="h-3 w-3 animate-spin text-primary" />
                    Loading halls of residence...
                  </div>
                ) : hallsError ? (
                  <div className="text-xs text-destructive bg-destructive/5 border border-destructive/20 rounded-lg p-2.5">
                    Failed to load halls. Please refresh.
                  </div>
                ) : !halls || halls.length === 0 ? (
                  <div className="text-xs text-muted-foreground bg-muted/30 border border-border/40 rounded-lg p-2.5">
                    No halls available. Contact administration.
                  </div>
                ) : (
                  <select
                    id="hall_id"
                    className={`flex h-9 w-full rounded-md border border-input bg-card px-3 py-1 text-sm shadow-xs transition-colors focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 text-foreground ${
                      errors.hall_id ? "border-destructive focus-visible:ring-destructive" : ""
                    }`}
                    {...register("hall_id")}
                    disabled={isLoading}
                  >
                    <option value="">Select your hall of residence...</option>
                    {halls.map((h) => (
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

              {/* Password */}
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Min. 8 characters"
                    autoComplete="new-password"
                    aria-invalid={!!errors.password}
                    {...register("password")}
                    className={
                      errors.password
                        ? "border-destructive pr-10 focus-visible:ring-destructive"
                        : "pr-10"
                    }
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((v) => !v)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                {errors.password && (
                  <p className="text-xs text-destructive">{errors.password.message}</p>
                )}
              </div>

              {/* Confirm Password */}
              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm password</Label>
                <div className="relative">
                  <Input
                    id="confirmPassword"
                    type={showConfirm ? "text" : "password"}
                    placeholder="••••••••"
                    autoComplete="new-password"
                    aria-invalid={!!errors.confirmPassword}
                    {...register("confirmPassword")}
                    className={
                      errors.confirmPassword
                        ? "border-destructive pr-10 focus-visible:ring-destructive"
                        : "pr-10"
                    }
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirm((v) => !v)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                    aria-label={showConfirm ? "Hide password" : "Show password"}
                  >
                    {showConfirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                {errors.confirmPassword && (
                  <p className="text-xs text-destructive">{errors.confirmPassword.message}</p>
                )}
              </div>
            </CardContent>

            <CardFooter className="flex flex-col gap-4 pt-2">
              <Button
                type="submit"
                className="w-full"
                size="lg"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating account…
                  </>
                ) : (
                  "Create account"
                )}
              </Button>

              <p className="text-center text-sm text-muted-foreground">
                Already have an account?{" "}
                <Link
                  href="/login"
                  className="font-medium text-primary underline-offset-4 hover:underline"
                >
                  Sign in
                </Link>
              </p>
            </CardFooter>
          </form>
        </Card>

        <p className="mt-6 text-center text-xs text-muted-foreground">
          By creating an account, you agree to our{" "}
          <span className="font-medium text-foreground/70">Terms of Service</span>{" "}
          and{" "}
          <span className="font-medium text-foreground/70">Privacy Policy</span>.
        </p>
      </div>
    </div>
  );
}
