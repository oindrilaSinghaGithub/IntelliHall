"use client";

import {
  BarChart3,
  Bell,
  Building2,
  LayoutDashboard,
  Settings,
  Wrench,
} from "lucide-react";
import Link from "next/link";

import { cn } from "@/lib/utils";
import { useAppStore } from "@/store/app-store";

const sidebarItems = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Maintenance", href: "/maintenance", icon: Wrench },
  { label: "Reports", href: "/reports", icon: BarChart3 },
  { label: "Notifications", href: "/notifications", icon: Bell },
  { label: "Settings", href: "/settings", icon: Settings },
];

/**
 * Placeholder sidebar for future authenticated dashboard layouts.
 * Not rendered on the landing page — import when building app shell.
 */
export function SidebarPlaceholder({ className }: { className?: string }) {
  const sidebarOpen = useAppStore((state) => state.sidebarOpen);

  return (
    <aside
      className={cn(
        "hidden w-64 shrink-0 flex-col border-r border-border bg-card md:flex",
        !sidebarOpen && "md:flex",
        className,
      )}
      aria-label="Sidebar navigation placeholder"
    >
      <div className="flex h-16 items-center gap-2 border-b px-6">
        <Building2 className="h-5 w-5 text-primary" />
        <span className="text-sm font-semibold">IntelliHall</span>
      </div>

      <nav className="flex-1 space-y-1 p-4">
        {sidebarItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </Link>
        ))}
      </nav>

      <div className="border-t p-4">
        <p className="text-xs text-muted-foreground">
          Sidebar placeholder — routes not implemented yet.
        </p>
      </div>
    </aside>
  );
}
