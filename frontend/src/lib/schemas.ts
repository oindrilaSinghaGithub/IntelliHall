import { z } from "zod";

// ---------------------------------------------------------------------------
// Login
// ---------------------------------------------------------------------------

export const loginSchema = z.object({
  email: z
    .string()
    .min(1, "Email is required")
    .email("Please enter a valid email address"),
  password: z
    .string()
    .min(1, "Password is required")
    .min(8, "Password must be at least 8 characters"),
});

export type LoginFormValues = z.infer<typeof loginSchema>;

// ---------------------------------------------------------------------------
// Register
// ---------------------------------------------------------------------------

export const registerSchema = z
  .object({
    name: z
      .string()
      .min(1, "Name is required")
      .min(2, "Name must be at least 2 characters")
      .max(255, "Name must be less than 255 characters"),
    email: z
      .string()
      .min(1, "Email is required")
      .email("Please enter a valid email address"),
    password: z
      .string()
      .min(1, "Password is required")
      .min(8, "Password must be at least 8 characters"),
    confirmPassword: z.string().min(1, "Please confirm your password"),
    role: z.union([z.literal("student"), z.literal("hall_admin")]),
    hall_id: z.string().min(1, "Hall of Residence is required"),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

export type RegisterFormValues = z.infer<typeof registerSchema>;

// ---------------------------------------------------------------------------
// Complaint
// ---------------------------------------------------------------------------

export const complaintSchema = z
  .object({
    title: z
      .string()
      .min(3, "Title must be at least 3 characters")
      .max(255, "Title must be less than 255 characters"),
    description: z
      .string()
      .min(10, "Description must be at least 10 characters"),
    complaint_type: z.union([z.literal("personal"), z.literal("common_area")]),
    category: z.enum([
      "electrical",
      "plumbing",
      "carpentry",
      "civil",
      "internet",
      "cleanliness",
      "water",
      "furniture",
      "other",
    ]),
    priority: z.enum(["low", "medium", "high", "critical"]),
    room_number: z.string().max(20).optional().nullable(),
    block: z.string().max(50).optional().nullable(),
    floor: z.string().max(10).optional().nullable(),
    common_area: z.string().max(100).optional().nullable(),
    qr_location_id: z.string().max(100).optional().nullable(),
    preferred_visit_time: z.string().optional().nullable(),
  })
  .superRefine((data, ctx) => {
    if (data.complaint_type === "personal") {
      if (!data.room_number || data.room_number.trim() === "") {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "Room number is required for personal complaints",
          path: ["room_number"],
        });
      }
    } else if (data.complaint_type === "common_area") {
      const hasBlock = data.block && data.block.trim() !== "";
      const hasFloor = data.floor && data.floor.trim() !== "";
      const hasCommonArea = data.common_area && data.common_area.trim() !== "";
      const hasQrLocation = data.qr_location_id && data.qr_location_id.trim() !== "";

      if (!hasBlock && !hasFloor && !hasCommonArea && !hasQrLocation) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message:
            "At least one of block, floor, common area, or QR location is required for common area complaints",
          path: ["common_area"],
        });
      }
    }
  });

export type ComplaintFormValues = z.infer<typeof complaintSchema>;

