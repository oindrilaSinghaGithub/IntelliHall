import { Card, CardContent, CardHeader } from "@/components/ui/card";

export function LoadingSkeleton({ variant = "list", count = 3 }: { variant?: "list" | "detail" | "form"; count?: number }) {
  if (variant === "detail") {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="space-y-2">
            <div className="h-8 w-64 rounded-md bg-muted" />
            <div className="h-4 w-40 rounded-md bg-muted" />
          </div>
          <div className="h-6 w-24 rounded-full bg-muted" />
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          <div className="space-y-6 md:col-span-2">
            <Card>
              <CardHeader>
                <div className="h-5 w-32 rounded-md bg-muted" />
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="h-4 w-full rounded-md bg-muted" />
                <div className="h-4 w-5/6 rounded-md bg-muted" />
                <div className="h-4 w-4/6 rounded-md bg-muted" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="h-5 w-40 rounded-md bg-muted" />
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="h-3 w-16 rounded-md bg-muted mb-2" />
                    <div className="h-4 w-32 rounded-md bg-muted" />
                  </div>
                  <div>
                    <div className="h-3 w-16 rounded-md bg-muted mb-2" />
                    <div className="h-4 w-32 rounded-md bg-muted" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card className="h-fit">
            <CardHeader>
              <div className="h-5 w-36 rounded-md bg-muted" />
            </CardHeader>
            <CardContent className="space-y-6">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex gap-4">
                  <div className="h-4 w-4 rounded-full bg-muted mt-1 shrink-0" />
                  <div className="space-y-1.5 flex-1">
                    <div className="h-4 w-28 rounded-md bg-muted" />
                    <div className="h-3 w-36 rounded-md bg-muted" />
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (variant === "form") {
    return (
      <Card className="animate-pulse">
        <CardHeader>
          <div className="h-6 w-48 rounded-md bg-muted" />
        </CardHeader>
        <CardContent className="space-y-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="space-y-2">
              <div className="h-4 w-24 rounded-md bg-muted" />
              <div className="h-10 w-full rounded-md bg-muted" />
            </div>
          ))}
          <div className="h-10 w-32 rounded-md bg-muted" />
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4 animate-pulse">
      {Array.from({ length: count }).map((_, idx) => (
        <Card key={idx} className="border border-border/50">
          <CardContent className="p-6">
            <div className="flex items-start justify-between gap-4">
              <div className="space-y-2.5 flex-1">
                <div className="flex items-center gap-2">
                  <div className="h-4 w-24 rounded-md bg-muted" />
                  <div className="h-4 w-16 rounded-md bg-muted" />
                </div>
                <div className="h-5 w-2/3 rounded-md bg-muted" />
                <div className="h-4 w-40 rounded-md bg-muted" />
              </div>
              <div className="h-6 w-20 rounded-full bg-muted shrink-0" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
