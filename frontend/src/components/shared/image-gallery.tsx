"use client";

import { useState } from "react";
import { X } from "lucide-react";

import type { ComplaintImage } from "@/types/complaint";
import { ImagePreviewModal } from "@/components/shared/image-preview-modal";

interface ImageGalleryProps {
  images: ComplaintImage[];
  canDelete: boolean;
  onDelete: (imageId: string) => void;
}

export function ImageGallery({ images, canDelete, onDelete }: ImageGalleryProps) {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);

  const handleDelete = (e: React.MouseEvent, imageId: string) => {
    e.stopPropagation();
    const confirmed = window.confirm("Are you sure you want to delete this image?");
    if (confirmed) {
      onDelete(imageId);
    }
  };

  if (!images || images.length === 0) {
    return (
      <p className="text-xs text-muted-foreground">No images attached to this complaint.</p>
    );
  }

  return (
    <>
      <div className="grid gap-4 grid-cols-2 sm:grid-cols-3">
        {images.map((img) => (
          <div
            key={img.id}
            role="button"
            tabIndex={0}
            className="relative aspect-square rounded-lg border border-border overflow-hidden bg-muted group cursor-pointer"
            onClick={() => setSelectedImage(img.image_url)}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") setSelectedImage(img.image_url);
            }}
            aria-label="View full size image"
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={img.image_url}
              alt="Complaint attachment"
              className="object-cover w-full h-full transition-transform group-hover:scale-105"
            />
            {canDelete && (
              <button
                type="button"
                onClick={(e) => handleDelete(e, img.id)}
                className="absolute top-1.5 right-1.5 flex h-6 w-6 items-center justify-center rounded-full bg-destructive text-destructive-foreground opacity-0 group-hover:opacity-100 transition-opacity shadow-sm"
                aria-label="Delete image"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        ))}
      </div>

      <ImagePreviewModal
        imageUrl={selectedImage}
        isOpen={selectedImage !== null}
        onClose={() => setSelectedImage(null)}
      />
    </>
  );
}
