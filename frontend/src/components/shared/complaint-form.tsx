import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { ImageUploader } from "@/components/shared/image-uploader";
import { complaintSchema, type ComplaintFormValues } from "@/lib/schemas";

interface ComplaintFormProps {
  onSubmit: (data: ComplaintFormValues, imageFiles: File[]) => void;
  isLoading: boolean;
}

export function ComplaintForm({ onSubmit, isLoading }: ComplaintFormProps) {
  const [imageFiles, setImageFiles] = useState<File[]>([]);
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<ComplaintFormValues>({
    resolver: zodResolver(complaintSchema),
    defaultValues: {
      title: "",
      description: "",
      complaint_type: "personal",
      category: "electrical",
      priority: "medium",
      room_number: "",
      block: "",
      floor: "",
      common_area: "",
      qr_location_id: "",
      preferred_visit_time: "",
    },
  });

  const complaintType = watch("complaint_type");

  return (
    <form onSubmit={handleSubmit((data) => onSubmit(data, imageFiles))} className="space-y-6">
      <Card className="border border-border/50">
        <CardContent className="p-6 space-y-6">
          {/* Title */}
          <div className="space-y-2">
            <Label htmlFor="title">Summary / Title</Label>
            <Input
              id="title"
              placeholder="e.g. Fan in room is making loud noise"
              {...register("title")}
              disabled={isLoading}
              className={errors.title ? "border-destructive focus-visible:ring-destructive" : ""}
            />
            {errors.title && (
              <p className="text-xs font-medium text-destructive">{errors.title.message}</p>
            )}
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Detailed Description</Label>
            <textarea
              id="description"
              rows={4}
              placeholder="Provide a detailed description of the issue. E.g. what is wrong, when did it start, has it happened before?"
              className={`flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs transition-colors placeholder:text-muted-foreground focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 ${
                errors.description ? "border-destructive focus-visible:ring-destructive" : ""
              }`}
              {...register("description")}
              disabled={isLoading}
            />
            {errors.description && (
              <p className="text-xs font-medium text-destructive">{errors.description.message}</p>
            )}
          </div>

          {/* Types and Options Grid */}
          <div className="grid gap-6 md:grid-cols-3">
            {/* Complaint Type */}
            <div className="space-y-2">
              <Label htmlFor="complaint_type">Complaint Type</Label>
              <select
                id="complaint_type"
                className="flex h-9 w-full rounded-md border border-input bg-card px-3 py-1 text-sm shadow-xs transition-colors focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 text-foreground"
                {...register("complaint_type")}
                disabled={isLoading}
              >
                <option value="personal">Personal Room</option>
                <option value="common_area">Common Area</option>
              </select>
            </div>

            {/* Category */}
            <div className="space-y-2">
              <Label htmlFor="category">Category</Label>
              <select
                id="category"
                className="flex h-9 w-full rounded-md border border-input bg-card px-3 py-1 text-sm shadow-xs transition-colors focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 text-foreground"
                {...register("category")}
                disabled={isLoading}
              >
                <option value="electrical">Electrical</option>
                <option value="plumbing">Plumbing</option>
                <option value="carpentry">Carpentry</option>
                <option value="civil">Civil</option>
                <option value="internet">Internet</option>
                <option value="cleanliness">Cleanliness</option>
                <option value="water">Water</option>
                <option value="furniture">Furniture</option>
                <option value="other">Other</option>
              </select>
            </div>

            {/* Priority */}
            <div className="space-y-2">
              <Label htmlFor="priority">Priority</Label>
              <select
                id="priority"
                className="flex h-9 w-full rounded-md border border-input bg-card px-3 py-1 text-sm shadow-xs transition-colors focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 text-foreground"
                {...register("priority")}
                disabled={isLoading}
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
          </div>

          {/* Conditional Location Fields */}
          {complaintType === "personal" ? (
            <div className="space-y-2 p-4 rounded-xl bg-muted/30 border border-border/40">
              <Label htmlFor="room_number">Room Number</Label>
              <Input
                id="room_number"
                placeholder="e.g. B-302"
                {...register("room_number")}
                disabled={isLoading}
                className={
                  errors.room_number ? "border-destructive focus-visible:ring-destructive" : ""
                }
              />
              {errors.room_number && (
                <p className="text-xs font-medium text-destructive">{errors.room_number.message}</p>
              )}
            </div>
          ) : (
            <div className="space-y-4 p-4 rounded-xl bg-muted/30 border border-border/40">
              <p className="text-xs text-muted-foreground font-medium mb-1">
                Provide location details. At least one field is required.
              </p>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="block">Block / Wing</Label>
                  <Input id="block" placeholder="e.g. Block A" {...register("block")} disabled={isLoading} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="floor">Floor</Label>
                  <Input id="floor" placeholder="e.g. 2nd Floor" {...register("floor")} disabled={isLoading} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="common_area">Common Area Name</Label>
                  <Input
                    id="common_area"
                    placeholder="e.g. Mess Hall, Corridor"
                    {...register("common_area")}
                    disabled={isLoading}
                    className={
                      errors.common_area ? "border-destructive focus-visible:ring-destructive" : ""
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="qr_location_id">QR Location ID (Optional)</Label>
                  <Input
                    id="qr_location_id"
                    placeholder="Scan / Enter QR tag if available"
                    {...register("qr_location_id")}
                    disabled={isLoading}
                  />
                </div>
              </div>
              {errors.common_area && (
                <p className="text-xs font-medium text-destructive">{errors.common_area.message}</p>
              )}
            </div>
          )}

          {/* Preferred visit time */}
          <div className="space-y-2">
            <Label htmlFor="preferred_visit_time">Preferred Visit Time (Optional)</Label>
            <Input
              id="preferred_visit_time"
              type="datetime-local"
              {...register("preferred_visit_time")}
              disabled={isLoading}
              className="text-foreground"
            />
            <p className="text-xs text-muted-foreground">
              Select a preferred time window when you will be available.
            </p>
          </div>

          {/* Image Upload */}
          <div className="space-y-2">
            <Label>Attach Images (Optional)</Label>
            <ImageUploader
              files={imageFiles}
              onChange={setImageFiles}
              maxFiles={5}
              maxSizeMB={5}
              disabled={isLoading}
            />
          </div>
        </CardContent>
      </Card>

      <div className="flex gap-4">
        <Button type="submit" disabled={isLoading} className="gap-2">
          {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
          Raise Complaint
        </Button>
      </div>
    </form>
  );
}
