"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ImagePlus, X } from "lucide-react";
import { toast } from "sonner";

import { Label } from "@/components/ui/label";
import {
  ALLOWED_IMAGE_TYPES,
  MAX_COMPLAINT_IMAGES,
  MAX_IMAGE_SIZE_BYTES,
} from "@/constants";

interface ImageUploadProps {
  files: File[];
  onChange: (files: File[]) => void;
  disabled?: boolean;
  maxFiles?: number;
}

function formatMaxSize(): string {
  return `${MAX_IMAGE_SIZE_BYTES / (1024 * 1024)} MB`;
}

export function ImageUpload({
  files,
  onChange,
  disabled = false,
  maxFiles = MAX_COMPLAINT_IMAGES,
}: ImageUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [previews, setPreviews] = useState<string[]>([]);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    const urls = files.map((file) => URL.createObjectURL(file));
    setPreviews(urls);
    return () => {
      urls.forEach((url) => URL.revokeObjectURL(url));
    };
  }, [files]);

  const validateAndAdd = useCallback(
    (incoming: FileList | File[]) => {
      const selected = Array.from(incoming);
      if (selected.length === 0) return;

      const remaining = maxFiles - files.length;
      if (remaining <= 0) {
        toast.error(`You can attach at most ${maxFiles} images.`);
        return;
      }

      const accepted: File[] = [];
      for (const file of selected.slice(0, remaining)) {
        if (!ALLOWED_IMAGE_TYPES.includes(file.type as (typeof ALLOWED_IMAGE_TYPES)[number])) {
          toast.error(`${file.name}: only JPEG, PNG, and WebP images are allowed.`);
          continue;
        }
        if (file.size > MAX_IMAGE_SIZE_BYTES) {
          toast.error(`${file.name}: exceeds the ${formatMaxSize()} size limit.`);
          continue;
        }
        accepted.push(file);
      }

      if (selected.length > remaining) {
        toast.error(`Only ${remaining} more image${remaining === 1 ? "" : "s"} can be added.`);
      }

      if (accepted.length > 0) {
        onChange([...files, ...accepted]);
      }
    },
    [files, maxFiles, onChange],
  );

  const removeFile = (index: number) => {
    onChange(files.filter((_, i) => i !== index));
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    if (disabled) return;
    validateAndAdd(event.dataTransfer.files);
  };

  return (
    <div className="space-y-3">
      <div className="space-y-1">
        <Label>Attach Photos (Optional)</Label>
        <p className="text-xs text-muted-foreground">
          Up to {maxFiles} images · {formatMaxSize()} each · JPEG, PNG, or WebP
        </p>
      </div>

      <div
        role="button"
        tabIndex={disabled ? -1 : 0}
        onKeyDown={(event) => {
          if (disabled) return;
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            inputRef.current?.click();
          }
        }}
        onClick={() => !disabled && inputRef.current?.click()}
        onDragOver={(event) => {
          event.preventDefault();
          if (!disabled) setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed p-6 text-center transition-colors cursor-pointer ${
          disabled
            ? "cursor-not-allowed opacity-50"
            : isDragging
              ? "border-primary bg-primary/5"
              : "border-border/60 bg-muted/20 hover:border-primary/40 hover:bg-muted/30"
        }`}
      >
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
          <ImagePlus className="h-5 w-5 text-primary" />
        </div>
        <div>
          <p className="text-sm font-medium">Click or drag photos here</p>
          <p className="text-xs text-muted-foreground mt-0.5">
            {files.length}/{maxFiles} selected
          </p>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept={ALLOWED_IMAGE_TYPES.join(",")}
          multiple
          className="hidden"
          disabled={disabled || files.length >= maxFiles}
          onChange={(event) => {
            if (event.target.files) {
              validateAndAdd(event.target.files);
            }
            event.target.value = "";
          }}
        />
      </div>

      {previews.length > 0 && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {previews.map((preview, index) => (
            <div
              key={`${files[index]?.name}-${index}`}
              className="group relative aspect-square overflow-hidden rounded-lg border border-border/50 bg-muted"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={preview}
                alt={files[index]?.name ?? `Preview ${index + 1}`}
                className="h-full w-full object-cover"
              />
              {!disabled && (
                <button
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation();
                    removeFile(index);
                  }}
                  className="absolute right-1.5 top-1.5 flex h-6 w-6 items-center justify-center rounded-full bg-background/90 text-foreground shadow-sm opacity-0 transition-opacity group-hover:opacity-100 focus:opacity-100"
                  aria-label={`Remove ${files[index]?.name ?? "image"}`}
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
