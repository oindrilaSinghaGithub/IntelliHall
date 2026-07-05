import { Brain, Building, ClipboardList } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { FEATURES } from "@/constants";

const icons = [ClipboardList, Brain, Building];

export function FeaturesSection() {
  return (
    <section id="features" className="border-t border-border/60 bg-muted/20 py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Everything hall office needs
          </h2>
          <p className="mt-4 text-muted-foreground">
            A modern platform that preserves existing workflows while bringing
            maintenance and wellbeing management into the digital age.
          </p>
        </div>

        <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((feature, index) => {
            const Icon = icons[index] ?? ClipboardList;
            return (
              <Card
                key={feature.title}
                className="border-border/60 bg-card/50 backdrop-blur-sm transition-colors hover:border-primary/30"
              >
                <CardHeader>
                  <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                    <Icon className="h-5 w-5 text-primary" />
                  </div>
                  <CardTitle>{feature.title}</CardTitle>
                  <CardDescription>{feature.description}</CardDescription>
                </CardHeader>
                <CardContent />
              </Card>
            );
          })}
        </div>
      </div>
    </section>
  );
}
