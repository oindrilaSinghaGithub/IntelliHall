import { Building2 } from "lucide-react";
import Link from "next/link";

import { Separator } from "@/components/ui/separator";
import { APP_DESCRIPTION, APP_NAME, NAV_LINKS } from "@/constants";

export function Footer() {
  return (
    <footer id="contact" className="border-t border-border/60">
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid gap-8 md:grid-cols-3">
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Building2 className="h-5 w-5 text-primary" />
              <span className="font-semibold">{APP_NAME}</span>
            </div>
            <p className="text-sm leading-relaxed text-muted-foreground">
              {APP_DESCRIPTION}
            </p>
          </div>

          <div>
            <h3 className="text-sm font-semibold">Navigation</h3>
            <ul className="mt-3 space-y-2">
              {NAV_LINKS.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div id="about">
            <h3 className="text-sm font-semibold">About</h3>
            <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
              IntelliHall digitizes hostel maintenance workflows for IIT
              Kharagpur while preserving the hall office process students and
              staff already trust.
            </p>
          </div>
        </div>

        <Separator className="my-8" />

        <p className="text-center text-xs text-muted-foreground">
          &copy; {new Date().getFullYear()} {APP_NAME}. IIT Kharagpur.
        </p>
      </div>
    </footer>
  );
}
