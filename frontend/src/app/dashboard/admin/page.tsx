"use client";

import Link from "next/link";
import {
  Building2,
  LogOut,
  LayoutDashboard,
  ClipboardList,
  Clock,
  Wrench,
  CheckCircle2,
  BarChart3,
  ListTodo,
  ShieldCheck,
  CalendarDays,
  AlertCircle,
  Timer,
  AlertTriangle,
  TrendingUp,
  PieChart as PieIcon,
  RefreshCw,
  ArrowUpRight,
} from "lucide-react";
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  AreaChart,
  Area,
  LabelList,
} from "recharts";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/use-auth";
import { useHallAnalytics } from "@/hooks/use-analytics";
import { usePendingVerifications } from "@/hooks/use-verification";
import { useMounted } from "@/hooks/use-mounted";
import { ComplaintStatusBadge } from "@/components/shared/complaint-status-badge";
import { NotificationBell } from "@/components/shared/notification-bell";

// Label mappings for clean charts rendering
const CATEGORY_LABELS: Record<string, string> = {
  electrical: "Electrical",
  plumbing: "Plumbing",
  carpentry: "Carpentry",
  civil: "Civil",
  internet: "Internet",
  cleanliness: "Cleanliness",
  water: "Water",
  furniture: "Furniture",
  other: "Other",
};

const STATUS_LABELS: Record<string, string> = {
  submitted: "Submitted",
  verified: "Verified",
  scheduled: "Scheduled",
  in_progress: "In Progress",
  completed: "Completed",
  waiting_student_confirmation: "Awaiting Confirm",
  reopened: "Reopened",
  closed: "Closed",
  visit_failed_room_locked: "Locked / Failed",
};

const STATUS_COLORS: Record<string, string> = {
  submitted: "#3b82f6",                  // Blue
  verified: "#6366f1",                   // Indigo
  scheduled: "#a855f7",                  // Purple
  in_progress: "#f59e0b",                // Amber
  completed: "#10b981",                  // Emerald
  waiting_student_confirmation: "#f97316", // Orange
  reopened: "#ea580c",                   // Red-Orange
  closed: "#64748b",                     // Slate
  visit_failed_room_locked: "#f43f5e",   // Rose
};

export default function AdminDashboardPage() {
  const { user, signOut } = useAuth();
  const isMounted = useMounted();
  const hallId = user?.hall_id || "";

  // React Query Fetch Hall Analytics
  const {
    data: analytics,
    isLoading: isAnalyticsLoading,
    error: analyticsError,
    refetch: refetchAnalytics,
  } = useHallAnalytics(hallId);

  // Live count for pending student verifications
  const { data: verificationData } = usePendingVerifications({ page: 1, page_size: 1 });
  const pendingVerificationsCount = verificationData?.total ?? 0;

  // Process data for charts
  const summary = analytics?.summary;
  const recentComplaints = analytics?.recent_complaints || [];

  const pieData = (analytics?.by_status || [])
    .filter((item) => item.count > 0)
    .map((item) => ({
      name: STATUS_LABELS[item.status] || item.status,
      value: item.count,
      color: STATUS_COLORS[item.status] || "#64748b",
    }));

  const barData = (analytics?.by_category || []).map((item) => ({
    name: CATEGORY_LABELS[item.category] || item.category,
    count: item.count,
  }));

  const lineData = (analytics?.monthly_trend || []).map((item) => {
    const [year, month] = item.month.split("-");
    const monthNames = [
      "Jan", "Feb", "Mar", "Apr", "May", "Jun", 
      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ];
    const formattedLabel = `${monthNames[parseInt(month) - 1]} '${year.slice(-2)}`;
    return {
      name: formattedLabel,
      count: item.count,
    };
  });

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

      {/* Main content */}
      <main className="flex-1">
        <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 space-y-6">
          
          {/* Welcome banner and Hall info */}
          <div className="grid gap-6 md:grid-cols-3">
            {/* Welcome Message Banner */}
            <div className="md:col-span-2 rounded-2xl border border-border/50 bg-card p-8 shadow-xs flex items-start gap-4">
              <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl bg-primary/10">
                <LayoutDashboard className="h-7 w-7 text-primary" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">
                  Welcome back, {user?.name?.split(" ")[0]}! 🏛️
                </h1>
                <p className="mt-1.5 text-sm text-muted-foreground">
                  You are logged in as a Hall Administrator. You can monitor hostel maintenance requests, assign technicians, and coordinate workflows.
                </p>
                <div className="mt-4 flex flex-wrap gap-3">
                  <Link href="/dashboard/admin/complaints">
                    <Button size="sm" className="gap-1.5 text-xs font-semibold">
                      <ClipboardList className="h-3.5 w-3.5" />
                      View Complaint Queue
                    </Button>
                  </Link>
                  <Link href="/dashboard/admin/verifications">
                    <Button size="sm" variant="outline" className="gap-1.5 text-xs font-semibold">
                      <ShieldCheck className="h-3.5 w-3.5" />
                      Hall Verifications
                      {pendingVerificationsCount > 0 && (
                        <span className="ml-1 rounded-full bg-amber-500 px-1.5 py-0.5 text-[10px] font-bold text-white leading-none">
                          {pendingVerificationsCount}
                        </span>
                      )}
                    </Button>
                  </Link>
                  <Link href="/dashboard/admin/schedule">
                    <Button size="sm" variant="outline" className="gap-1.5 text-xs font-semibold">
                      <CalendarDays className="h-3.5 w-3.5" />
                      Work Schedule
                    </Button>
                  </Link>
                </div>
              </div>
            </div>

            {/* Hall Information Card */}
            <Card className="border border-border/50 bg-card">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-bold flex items-center gap-2">
                  <Building2 className="h-4 w-4 text-primary" />
                  Hall Information
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="p-3 rounded-lg bg-muted/40 border border-border/40 text-center">
                  <p className="text-xs font-semibold text-foreground">
                    {user?.hall_name || "Hall information unavailable"}
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Error and Loading Handlers */}
          {analyticsError ? (
            <ErrorState error={analyticsError} refetch={refetchAnalytics} />
          ) : isAnalyticsLoading ? (
            <div className="space-y-6">
              <KpiSkeleton />
              <ChartsSkeleton />
              <TableSkeleton />
            </div>
          ) : (
            <div className="space-y-6">
              
              {/* KPI Cards Grid */}
              <div className="grid gap-4 grid-cols-2 lg:grid-cols-6">
                {[
                  {
                    title: "Total Complaints",
                    value: String(summary?.total_complaints ?? 0),
                    desc: "All registered complaints",
                    icon: ClipboardList,
                    color: "text-blue-500 bg-blue-500/10",
                    href: "/dashboard/admin/complaints",
                  },
                  {
                    title: "Open Complaints",
                    value: String(summary?.open_complaints ?? 0),
                    desc: "Active & unresolved",
                    icon: Clock,
                    color: "text-amber-500 bg-amber-500/10",
                    href: "/dashboard/admin/complaints",
                  },
                  {
                    title: "In Progress",
                    value: String(summary?.in_progress ?? 0),
                    desc: "Currently being fixed",
                    icon: Wrench,
                    color: "text-purple-500 bg-purple-500/10",
                    href: null,
                  },
                  {
                    title: "Completed",
                    value: String(summary?.completed ?? 0),
                    desc: "Resolved & closed cases",
                    icon: CheckCircle2,
                    color: "text-emerald-500 bg-emerald-500/10",
                    href: null,
                  },
                  {
                    title: "Critical Complaints",
                    value: String(summary?.critical_complaints ?? 0),
                    desc: "Urgent issues open",
                    icon: AlertCircle,
                    color: (summary?.critical_complaints ?? 0) > 0 ? "text-rose-500 bg-rose-500/10 font-bold animate-pulse" : "text-slate-500 bg-slate-500/10",
                    href: "/dashboard/admin/complaints",
                  },
                  {
                    title: "Avg Resolution",
                    value: summary?.avg_resolution_time_hours !== null 
                      ? `${summary?.avg_resolution_time_hours}h` 
                      : "N/A",
                    desc: "Creation to closure time",
                    icon: Timer,
                    color: "text-indigo-500 bg-indigo-500/10",
                    href: null,
                  },
                ].map((stat, idx) => (
                  stat.href ? (
                    <Link key={idx} href={stat.href} className="block">
                      <Card className="border border-border/50 bg-card transition-all hover:border-primary/30 hover:shadow-md cursor-pointer h-full">
                        <CardContent className="p-5 flex items-start justify-between">
                          <div className="space-y-1 flex-1">
                            <p className="text-[10px] font-bold text-muted-foreground tracking-wider uppercase truncate">
                              {stat.title}
                            </p>
                            <p className="text-2xl font-bold tracking-tight">{stat.value}</p>
                            <p className="text-[9px] text-muted-foreground leading-snug">{stat.desc}</p>
                          </div>
                          <div className={`p-2 rounded-lg shrink-0 ${stat.color}`}>
                            <stat.icon className="h-4.5 w-4.5" />
                          </div>
                        </CardContent>
                      </Card>
                    </Link>
                  ) : (
                    <Card key={idx} className="border border-border/50 bg-card h-full">
                      <CardContent className="p-5 flex items-start justify-between">
                        <div className="space-y-1 flex-1">
                          <p className="text-[10px] font-bold text-muted-foreground tracking-wider uppercase truncate">
                            {stat.title}
                          </p>
                          <p className="text-2xl font-bold tracking-tight">{stat.value}</p>
                          <p className="text-[9px] text-muted-foreground leading-snug">{stat.desc}</p>
                        </div>
                        <div className={`p-2 rounded-lg shrink-0 ${stat.color}`}>
                          <stat.icon className="h-4.5 w-4.5" />
                        </div>
                      </CardContent>
                    </Card>
                  )
                ))}
              </div>

              {/* Charts Segment */}
              {isMounted ? (
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                  
                  {/* Status distribution (Pie Chart) */}
                  <Card className="border border-border/50 bg-card flex flex-col">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-bold flex items-center gap-2">
                        <PieIcon className="h-4 w-4 text-primary" />
                        Status Distribution
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="h-80 flex-1 relative min-h-[280px]">
                      {pieData.length === 0 ? (
                        <div className="absolute inset-0 flex flex-col items-center justify-center text-muted-foreground text-xs">
                          No status data available
                        </div>
                      ) : (
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie
                              data={pieData}
                              cx="50%"
                              cy="50%"
                              innerRadius={60}
                              outerRadius={82}
                              paddingAngle={3}
                              dataKey="value"
                            >
                              {pieData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.color} />
                              ))}
                            </Pie>
                            <Tooltip
                              contentStyle={{
                                backgroundColor: "#0f172a",
                                borderColor: "#334155",
                                borderRadius: "8px",
                              }}
                              itemStyle={{ color: "#f8fafc", fontSize: 12 }}
                              labelStyle={{ color: "#94a3b8", fontWeight: 600, fontSize: 12 }}
                            />
                            <Legend
                              verticalAlign="bottom"
                              height={45}
                              iconType="circle"
                              iconSize={8}
                              formatter={(value) => (
                                <span className="text-[12px] font-semibold text-slate-200 mx-1">
                                  {value}
                                </span>
                              )}
                            />
                          </PieChart>
                        </ResponsiveContainer>
                      )}
                    </CardContent>
                  </Card>

                  {/* Category counts (Bar Chart) */}
                  <Card className="border border-border/50 bg-card md:col-span-2 lg:col-span-2 flex flex-col">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-bold flex items-center gap-2">
                        <BarChart3 className="h-4 w-4 text-primary" />
                        Complaints by Category
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="h-80 flex-1 relative min-h-[280px]">
                      {barData.length === 0 ? (
                        <div className="absolute inset-0 flex flex-col items-center justify-center text-muted-foreground text-xs">
                          No complaints recorded
                        </div>
                      ) : (
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={barData} margin={{ top: 25, right: 10, left: -20, bottom: 5 }}>
                            <defs>
                              <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.95} />
                                <stop offset="100%" stopColor="#1d4ed8" stopOpacity={0.3} />
                              </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#475569" strokeOpacity={0.15} />
                            <XAxis
                              dataKey="name"
                              tick={{ fill: "#CBD5E1", fontSize: 12 }}
                              tickMargin={8}
                              tickLine={false}
                              axisLine={false}
                            />
                            <YAxis
                              tick={{ fill: "#CBD5E1", fontSize: 12 }}
                              tickMargin={8}
                              tickLine={false}
                              axisLine={false}
                              allowDecimals={false}
                            />
                            <Tooltip
                              contentStyle={{
                                backgroundColor: "#0f172a",
                                borderColor: "#334155",
                                borderRadius: "8px",
                              }}
                              itemStyle={{ color: "#f8fafc", fontSize: 12 }}
                              labelStyle={{ color: "#94a3b8", fontWeight: 600, fontSize: 12 }}
                              cursor={{ fill: "hsl(var(--muted)/0.15)" }}
                            />
                            <Bar
                              dataKey="count"
                              fill="url(#barGradient)"
                              radius={[6, 6, 0, 0]}
                              maxBarSize={40}
                              barSize={32}
                            >
                              <LabelList
                                dataKey="count"
                                position="top"
                                fill="#CBD5E1"
                                fontSize={11}
                                fontWeight={600}
                                offset={8}
                              />
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      )}
                    </CardContent>
                  </Card>

                  {/* Monthly Trend (Area Chart) */}
                  <Card className="border border-border/50 bg-card md:col-span-2 lg:col-span-3 flex flex-col">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-bold flex items-center gap-2">
                        <TrendingUp className="h-4 w-4 text-primary" />
                        Monthly Complaint Trend
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="h-80 flex-1 relative min-h-[280px]">
                      {lineData.length === 0 ? (
                        <div className="absolute inset-0 flex flex-col items-center justify-center text-muted-foreground text-xs">
                          No trend data available
                        </div>
                      ) : (
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={lineData} margin={{ top: 20, right: 20, left: -20, bottom: 5 }}>
                            <defs>
                              <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor="#06b6d4" stopOpacity={0.25} />
                                <stop offset="100%" stopColor="#06b6d4" stopOpacity={0.0} />
                              </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#475569" strokeOpacity={0.15} />
                            <XAxis
                              dataKey="name"
                              tick={{ fill: "#CBD5E1", fontSize: 12 }}
                              tickMargin={8}
                              tickLine={false}
                              axisLine={false}
                            />
                            <YAxis
                              tick={{ fill: "#CBD5E1", fontSize: 12 }}
                              tickMargin={8}
                              tickLine={false}
                              axisLine={false}
                              allowDecimals={false}
                            />
                            <Tooltip
                              contentStyle={{
                                backgroundColor: "#0f172a",
                                borderColor: "#334155",
                                borderRadius: "8px",
                              }}
                              itemStyle={{ color: "#f8fafc", fontSize: 12 }}
                              labelStyle={{ color: "#94a3b8", fontWeight: 600, fontSize: 12 }}
                            />
                            <Area
                              type="monotone"
                              dataKey="count"
                              stroke="#06b6d4"
                              strokeWidth={3}
                              fill="url(#areaGradient)"
                              dot={{ r: 6, strokeWidth: 2, fill: "#0f172a", stroke: "#06b6d4" }}
                              activeDot={{ r: 8, strokeWidth: 2, fill: "#06b6d4" }}
                            />
                          </AreaChart>
                        </ResponsiveContainer>
                      )}
                    </CardContent>
                  </Card>
                </div>
              ) : (
                <ChartsSkeleton />
              )}

              {/* Recent Complaints Section */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-bold tracking-tight flex items-center gap-2">
                    <ListTodo className="h-5 w-5 text-primary" />
                    Recent Complaints
                  </h2>
                  {recentComplaints.length > 0 && (
                    <Link
                      href="/dashboard/admin/complaints"
                      className="text-xs font-semibold text-primary hover:underline flex items-center gap-0.5"
                    >
                      View full queue
                      <ArrowUpRight className="h-3.5 w-3.5" />
                    </Link>
                  )}
                </div>

                {recentComplaints.length === 0 ? (
                  <Card className="border border-dashed border-border bg-card/60">
                    <CardContent className="p-12 text-center flex flex-col items-center justify-center min-h-[220px]">
                      <p className="text-sm font-medium text-muted-foreground">
                        No complaints registered in this hall yet.
                      </p>
                    </CardContent>
                  </Card>
                ) : (
                  <div className="overflow-x-auto rounded-xl border border-border/50 bg-card">
                    <table className="min-w-full divide-y divide-border/40 text-left">
                      <thead className="bg-muted/40 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                        <tr>
                          <th className="px-6 py-4">Title</th>
                          <th className="px-6 py-4">Category</th>
                          <th className="px-6 py-4">Location</th>
                          <th className="px-6 py-4">Date Filed</th>
                          <th className="px-6 py-4">Priority</th>
                          <th className="px-6 py-4">Status</th>
                          <th className="px-6 py-4 text-right">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/40 text-sm">
                        {recentComplaints.map((c) => {
                          const locationText =
                            c.complaint_type === "personal"
                              ? `Room ${c.room_number || "N/A"}`
                              : [c.block, c.floor, c.common_area]
                                  .filter(Boolean)
                                  .join(", ") || "Common Area";

                          const formattedDate = new Date(c.created_at).toLocaleDateString(
                            "en-US",
                            {
                              month: "short",
                              day: "numeric",
                              year: "numeric",
                            }
                          );

                          const priorityColors: Record<string, string> = {
                            low: "text-slate-500 bg-slate-500/10",
                            medium: "text-blue-500 bg-blue-500/10",
                            high: "text-orange-500 bg-orange-500/10",
                            critical: "text-red-500 bg-red-500/10 font-bold animate-pulse",
                          };

                          return (
                            <tr key={c.id} className="hover:bg-muted/30 transition-colors">
                              <td className="px-6 py-4 font-semibold text-foreground max-w-[220px] truncate">
                                {c.title}
                              </td>
                              <td className="px-6 py-4">
                                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-muted text-muted-foreground uppercase">
                                  {CATEGORY_LABELS[c.category] || c.category}
                                </span>
                              </td>
                              <td className="px-6 py-4 text-muted-foreground">
                                {locationText}
                              </td>
                              <td className="px-6 py-4 text-muted-foreground">
                                {formattedDate}
                              </td>
                              <td className="px-6 py-4">
                                {(() => {
                                  const displayPriority = c.predicted_priority || c.priority;
                                  return (
                                    <span
                                      className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full ${
                                        priorityColors[displayPriority] || "bg-secondary"
                                      }`}
                                    >
                                      {displayPriority.toUpperCase()}
                                    </span>
                                  );
                                })()}
                              </td>
                              <td className="px-6 py-4">
                                <ComplaintStatusBadge status={c.status} />
                              </td>
                              <td className="px-6 py-4 text-right">
                                <Link href={`/dashboard/admin/complaints/${c.id}`}>
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    className="text-xs text-primary hover:text-primary/80 font-semibold"
                                  >
                                    View
                                  </Button>
                                </Link>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components: Loading & Error States
// ---------------------------------------------------------------------------

function ErrorState({ error, refetch }: { error: any; refetch: () => void }) {
  return (
    <Card className="border border-red-500/20 bg-red-500/5 text-center p-8">
      <CardContent className="flex flex-col items-center justify-center gap-4">
        <AlertTriangle className="h-12 w-12 text-destructive animate-bounce" />
        <h3 className="text-lg font-bold text-foreground">Failed to Load Dashboard Analytics</h3>
        <p className="text-sm text-muted-foreground max-w-md">
          {error?.message ||
            "There was a problem communicating with the server. Please check your connection or try again."}
        </p>
        <Button onClick={() => refetch()} className="gap-2 mt-2 font-semibold">
          <RefreshCw className="h-4 w-4" />
          Retry Loading
        </Button>
      </CardContent>
    </Card>
  );
}

function KpiSkeleton() {
  return (
    <div className="grid gap-4 grid-cols-2 lg:grid-cols-6 animate-pulse">
      {Array.from({ length: 6 }).map((_, i) => (
        <Card key={i} className="border border-border/50 bg-card">
          <CardContent className="p-5 flex items-start justify-between">
            <div className="space-y-2 flex-1">
              <div className="h-3 w-16 bg-muted rounded" />
              <div className="h-7 w-10 bg-muted rounded" />
              <div className="h-2.5 w-20 bg-muted rounded" />
            </div>
            <div className="h-9 w-9 bg-muted rounded-lg shrink-0" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function ChartsSkeleton() {
  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 animate-pulse">
      <Card className="border border-border/50 bg-card flex flex-col">
        <CardHeader className="pb-2">
          <div className="h-4 w-32 bg-muted rounded" />
        </CardHeader>
        <CardContent className="h-80 flex items-center justify-center">
          <div className="h-40 w-40 rounded-full border-[10px] border-muted" />
        </CardContent>
      </Card>
      <Card className="border border-border/50 bg-card md:col-span-2 lg:col-span-2 flex flex-col">
        <CardHeader className="pb-2">
          <div className="h-4 w-40 bg-muted rounded" />
        </CardHeader>
        <CardContent className="h-80 flex items-end justify-between px-10 pb-6">
          <div className="h-16 w-8 bg-muted rounded-t" />
          <div className="h-32 w-8 bg-muted rounded-t" />
          <div className="h-24 w-8 bg-muted rounded-t" />
          <div className="h-48 w-8 bg-muted rounded-t" />
          <div className="h-40 w-8 bg-muted rounded-t" />
          <div className="h-28 w-8 bg-muted rounded-t" />
        </CardContent>
      </Card>
      <Card className="border border-border/50 bg-card md:col-span-2 lg:col-span-3 flex flex-col">
        <CardHeader className="pb-2">
          <div className="h-4 w-44 bg-muted rounded" />
        </CardHeader>
        <CardContent className="h-80 flex items-center justify-center">
          <div className="w-full h-full border-b border-l border-muted flex items-end relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-t from-muted/10 to-transparent" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function TableSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="flex justify-between items-center">
        <div className="h-5 w-36 bg-muted rounded" />
        <div className="h-4 w-20 bg-muted rounded" />
      </div>
      <Card className="border border-border/50 bg-card">
        <CardContent className="p-0">
          <div className="h-12 bg-muted/30 border-b border-border/50 w-full" />
          {Array.from({ length: 5 }).map((_, i) => (
            <div
              key={i}
              className="flex justify-between items-center px-6 py-4 border-b border-border/40 last:border-none"
            >
              <div className="h-4 w-1/4 bg-muted rounded" />
              <div className="h-4 w-12 bg-muted rounded" />
              <div className="h-4 w-1/5 bg-muted rounded" />
              <div className="h-4 w-16 bg-muted rounded" />
              <div className="h-4 w-10 bg-muted rounded" />
              <div className="h-6 w-20 bg-muted rounded-full" />
              <div className="h-8 w-12 bg-muted rounded" />
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
