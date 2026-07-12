"use client";

import { useRef, useState } from "react";
import { Bell, CheckCheck, ExternalLink, Loader2 } from "lucide-react";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import { useMarkAllRead, useMarkNotificationRead, useNotifications, useUnreadCount } from "@/hooks/use-notifications";
import { useAuthStore } from "@/store/auth-store";

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const { user } = useAuthStore();
  const isAdmin = user?.role === "hall_admin";

  const { data: unreadData } = useUnreadCount();
  const { data: notifData, isLoading } = useNotifications({ page: 1, page_size: 10 });

  const markReadMutation = useMarkNotificationRead();
  const markAllMutation = useMarkAllRead();

  const unreadCount = unreadData?.unread_count ?? 0;
  const notifications = notifData?.items ?? [];

  const getComplaintHref = (complaintId: string) =>
    isAdmin
      ? `/dashboard/admin/complaints/${complaintId}`
      : `/dashboard/complaints/${complaintId}`;

  const handleNotificationClick = (id: string, isRead: boolean) => {
    if (!isRead) {
      markReadMutation.mutate(id);
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell button */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="relative flex h-9 w-9 items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-accent transition-colors focus:outline-hidden focus-visible:ring-2 focus-visible:ring-ring"
        aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ""}`}
      >
        <Bell className="h-4 w-4" />
        {unreadCount > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[9px] font-bold text-white leading-none">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {open && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setOpen(false)}
            aria-hidden
          />

          <div className="absolute right-0 top-10 z-50 w-80 rounded-xl border border-border/80 bg-card shadow-xl animate-in fade-in-0 zoom-in-95 duration-150">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-border/50 px-4 py-3">
              <span className="text-sm font-semibold text-foreground">Notifications</span>
              {unreadCount > 0 && (
                <button
                  onClick={() => markAllMutation.mutate()}
                  disabled={markAllMutation.isPending}
                  className="flex items-center gap-1 text-[10px] font-semibold text-primary hover:underline disabled:opacity-50"
                >
                  {markAllMutation.isPending ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <CheckCheck className="h-3 w-3" />
                  )}
                  Mark all read
                </button>
              )}
            </div>

            {/* List */}
            <div className="max-h-80 overflow-y-auto divide-y divide-border/30">
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                </div>
              ) : notifications.length === 0 ? (
                <div className="py-8 text-center text-xs text-muted-foreground">
                  No notifications yet.
                </div>
              ) : (
                notifications.map((n) => (
                  <div
                    key={n.id}
                    onClick={() => handleNotificationClick(n.id, n.is_read)}
                    className={`flex items-start gap-3 px-4 py-3 cursor-pointer transition-colors hover:bg-muted/50 ${
                      !n.is_read ? "bg-primary/5" : ""
                    }`}
                  >
                    {/* Unread dot */}
                    <span
                      className={`mt-1.5 flex h-2 w-2 shrink-0 rounded-full ${
                        !n.is_read ? "bg-primary" : "bg-transparent"
                      }`}
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-foreground leading-snug line-clamp-2">
                        {n.message}
                      </p>
                      <p className="text-[10px] text-muted-foreground mt-0.5">
                        {formatDistanceToNow(new Date(n.created_at), { addSuffix: true })}
                      </p>
                    </div>
                    {n.complaint_id && (
                      <Link
                        href={getComplaintHref(n.complaint_id)}
                        onClick={(e) => e.stopPropagation()}
                        className="shrink-0 text-muted-foreground hover:text-primary transition-colors"
                        aria-label="View complaint"
                      >
                        <ExternalLink className="h-3.5 w-3.5" />
                      </Link>
                    )}
                  </div>
                ))
              )}
            </div>

            {/* Footer */}
            {notifications.length > 0 && (
              <div className="border-t border-border/50 px-4 py-2.5 text-center">
                <Link
                  href="/dashboard"
                  onClick={() => setOpen(false)}
                  className="text-[10px] font-semibold text-primary hover:underline"
                >
                  Go to dashboard
                </Link>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
