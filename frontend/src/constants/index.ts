export const APP_NAME = "IntelliHall";

export const APP_DESCRIPTION =
  "AI-powered Hall Maintenance & Wellbeing Management System for IIT Kharagpur";

export const APP_TAGLINE = "Hall Maintenance & Wellbeing, Reimagined";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export const NAV_LINKS = [
  { label: "Features", href: "#features" },
  { label: "About", href: "#about" },
  { label: "Contact", href: "#contact" },
] as const;

export const FEATURES = [
  {
    title: "Smart Complaint Tracking",
    description:
      "Digitize maintenance requests with real-time status updates across hall workflows.",
  },
  {
    title: "AI-powered Prioritization",
    description:
      "Intelligent triage helps hall office staff focus on the most urgent issues first.",
  },
  {
    title: "Hall-wise Administration",
    description:
      "Role-based dashboards tailored for students, hall office, technicians, and wardens.",
  },
] as const;
