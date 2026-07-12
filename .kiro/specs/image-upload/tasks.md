# Implementation Plan: Image Upload & Management

## Overview

Implements image upload and management for the IntelliHall complaint system following the existing Repository → Service → Endpoint (backend) and Service → Hook → Component (frontend) patterns. The implementation uses Python/FastAPI on the backend and TypeScript/Next.js on the frontend.

## Tasks

- [x] 1. Backend Image Repository
  - [x] 1.1 Create `backend/app/repositories/image_repository.py`
    - Implement `ImageRepository` class with static async methods following existing `ComplaintRepository` pattern
    - `create(session, complaint_id, image_url)` → insert ComplaintImage record, flush, refresh, return
    - `get_by_id(session, image_id)` → select with joinedload on complaint relationship, return or None
    - `count_for_complaint(session, complaint_id)` → SELECT COUNT(*) WHERE complaint_id matches
    - `delete(session, image)` → session.delete + flush
    - Use type annotations: `AsyncSession`, `ComplaintImage | None`
    - _Requirements: 1.8, 1.9, 2.1_

- [x] 2. Backend Image Service
  - [x] 2.1 Create `backend/app/services/image_service.py`
    - Implement `ImageService` class with static async methods
    - Constants: `ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}`, `MAX_FILE_SIZE = 5 * 1024 * 1024`, `MAX_IMAGES_PER_COMPLAINT = 5`
    - `upload_images(session, complaint_id, files, current_user)`:
      - Fetch complaint via ComplaintRepository.get_by_id, raise 404 if not found
      - Auth check: user is complaint.created_by OR (user.role == hall_admin AND user.hall_id == complaint.hall_id), else raise 403
      - Count check via ImageRepository.count_for_complaint, reject if count + len(files) > 5
      - For each file: validate extension (split filename on `.`, check last part lowercase), validate size (read content, check len), generate UUID4 filename, write to `{UPLOAD_DIR}/complaints/{uuid}.{ext}`, create DB record via ImageRepository.create
      - Return list of created ComplaintImage records
    - `delete_image(session, image_id, current_user)`:
      - Fetch image via ImageRepository.get_by_id, raise 404 if None
      - Auth check same pattern as upload (using image.complaint relationship)
      - Remove physical file with `Path.unlink(missing_ok=True)`
      - Delete DB record via ImageRepository.delete
    - `ensure_upload_dir()`: `Path(settings.UPLOAD_DIR) / "complaints"` → `mkdir(parents=True, exist_ok=True)`
    - Use `from app.core.config import settings` for UPLOAD_DIR
    - _Requirements: 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.2_

  - [ ]* 2.2 Write property tests for image service validation logic
    - **Property 4: File type validation completeness**
    - **Validates: Requirements 1.5, 1.6**
    - Test that any file with extension NOT in allowed set is rejected
    - Test that any file over 5MB is rejected
    - Test that count > 5 is rejected

  - [ ]* 2.3 Write property tests for authorization logic
    - **Property 2: Authorization symmetry**
    - **Validates: Requirements 1.2, 1.3, 1.4, 2.2, 2.3, 2.4**
    - Test that owner always gets access, matching hall_admin always gets access, others always get 403

- [x] 3. Backend Image Endpoints + Static Files Mount
  - [x] 3.1 Add image endpoints to `backend/app/api/v1/endpoints/complaints.py`
    - `POST /{complaint_id}/images`: Accept `files: list[UploadFile] = File(...)`, delegate to `ImageService.upload_images`, return `list[ComplaintImageRead]` with 201
    - `DELETE /images/{image_id}`: Delegate to `ImageService.delete_image`, return `Response` with 204
    - Add `from fastapi import File, UploadFile` imports
    - Add `from app.services.image_service import ImageService` import
    - _Requirements: 1.1, 2.1_

  - [x] 3.2 Enable static files mount in `backend/app/main.py`
    - Uncomment `from fastapi.staticfiles import StaticFiles`
    - Uncomment the `app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")` block
    - Add `from pathlib import Path` and call `Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)` before the mount (or call `ImageService.ensure_upload_dir()`)
    - _Requirements: 3.1, 3.2_

  - [ ]* 3.3 Write integration tests for image endpoints
    - Test upload with valid files → 201 + correct response
    - Test upload with unauthorized user → 403
    - Test upload with invalid file type → 400
    - Test upload exceeding count limit → 400
    - Test delete with valid auth → 204
    - Test delete non-existent image → 404
    - _Requirements: 1.1–1.9, 2.1–2.6_

- [x] 4. Checkpoint - Backend verification
  - Ensure all backend tests pass, ask the user if questions arise.
  - Manually test: upload an image via curl/Postman, verify it's served at `/uploads/complaints/{uuid}.ext`

- [x] 5. Frontend Service + Hook Layer
  - [x] 5.1 Add service functions to `frontend/src/services/complaint.ts`
    - `uploadComplaintImages(complaintId: string, files: File[], onProgress?: (percent: number) => void): Promise<ComplaintImage[]>` — build FormData, POST with `Content-Type: multipart/form-data` header, pass `onUploadProgress` to axios config
    - `deleteComplaintImage(imageId: string): Promise<void>` — DELETE request
    - _Requirements: 6.1, 6.2_

  - [x] 5.2 Add hooks to `frontend/src/hooks/use-complaints.ts`
    - `useUploadImages(complaintId: string)` — useMutation wrapping `uploadComplaintImages`, invalidate `COMPLAINT_KEYS.detail(complaintId)` on success, toast success/error
    - `useDeleteImage(complaintId: string)` — useMutation wrapping `deleteComplaintImage`, invalidate `COMPLAINT_KEYS.detail(complaintId)` on success, toast success/error
    - Follow exact same pattern as existing `useCreateComplaint`, `useConfirmRepair` hooks
    - _Requirements: 6.3, 6.4_

- [x] 6. Frontend ImageUploader Component
  - [x] 6.1 Create `frontend/src/components/shared/image-uploader.tsx`
    - Props: `{ files: File[]; onChange: (files: File[]) => void; maxFiles?: number; maxSizeMB?: number; disabled?: boolean }`
    - Drag-and-drop zone: `onDragOver`, `onDragLeave`, `onDrop` handlers with visual state change
    - Hidden `<input type="file" multiple accept="image/jpeg,image/png,image/webp">` triggered by browse button
    - Client-side validation on selection:
      - Check MIME type is in `["image/jpeg", "image/png", "image/webp"]` → error "Only JPG, PNG, and WebP images are allowed"
      - Check file.size ≤ maxSizeMB * 1024 * 1024 → error "File exceeds 5MB size limit"
      - Check total count ≤ maxFiles → error "Maximum 5 images allowed"
    - Thumbnail preview grid: use `URL.createObjectURL(file)` for each valid file
    - Remove button on each thumbnail: filter file out of array, call `onChange`
    - Use Tailwind classes matching existing card/input styling
    - Use lucide-react icons (Upload, X, ImageIcon)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [x] 7. Frontend ImageGallery + ImagePreviewModal Components
  - [x] 7.1 Create `frontend/src/components/shared/image-gallery.tsx`
    - Props: `{ images: ComplaintImage[]; canDelete: boolean; onDelete: (imageId: string) => void }`
    - Responsive grid: `grid grid-cols-2 sm:grid-cols-3 gap-4`
    - Each image: `aspect-square rounded-lg border overflow-hidden` with object-cover img
    - Click image → open preview modal (local state: `selectedImage`)
    - Conditional delete button (small X icon overlay) when `canDelete` is true
    - Delete click → window.confirm("Are you sure you want to delete this image?") → call onDelete
    - _Requirements: 5.1, 5.4, 5.5, 5.6_

  - [x] 7.2 Create `frontend/src/components/shared/image-preview-modal.tsx`
    - Props: `{ imageUrl: string | null; isOpen: boolean; onClose: () => void }`
    - Fixed overlay: `fixed inset-0 z-50 bg-black/80 backdrop-blur-sm`
    - Close button (X icon, top-right)
    - Close on Escape: `useEffect` with `keydown` listener
    - Close on backdrop click: `onClick` on overlay div (check `e.target === e.currentTarget`)
    - Center image with `max-w-[90vw] max-h-[90vh] object-contain`
    - Render null when `!isOpen`
    - _Requirements: 5.2, 5.3_

- [x] 8. Frontend Integration (Complaint Form + Detail Page)
  - [x] 8.1 Integrate ImageUploader into `frontend/src/components/shared/complaint-form.tsx`
    - Add `const [imageFiles, setImageFiles] = useState<File[]>([])` state
    - Add ImageUploader component between the preferred visit time field and the submit button
    - Modify the parent page's submit handler (or expose `imageFiles` via a ref/callback) so that after `createComplaint` succeeds, call `uploadComplaintImages(newComplaint.id, imageFiles)` if imageFiles.length > 0
    - Show upload progress state during image upload
    - Handle the two-step flow: create complaint → then upload images → then redirect
    - _Requirements: 4.7, 4.8, 4.9_

  - [x] 8.2 Integrate ImageGallery into `frontend/src/app/dashboard/complaints/[id]/page.tsx`
    - Replace the existing static images grid with `<ImageGallery>` component
    - Pass `canDelete={user?.id === complaint.created_by || (user?.role === "hall_admin" && user?.hall_id === complaint.hall_id)}`
    - Wire `onDelete` to `useDeleteImage(complaint.id).mutate`
    - Add the ImagePreviewModal (managed by ImageGallery internally)
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [x] 9. Checkpoint - Frontend verification
  - Ensure all frontend builds without errors (`npm run build`)
  - Verify: drag-and-drop upload on new complaint form
  - Verify: image gallery displays on complaint detail page
  - Verify: lightbox opens on image click
  - Verify: delete works for authorized users
  - Ask the user if questions arise.

- [x] 10. Documentation Update
  - [x] 10.1 Update `README.md`
    - Add "Image Upload" section under features describing: drag-and-drop upload, file type/size validation, responsive gallery, lightbox viewer, role-based deletion
    - Update contributor role: replace "Kavya Rai — Frontend" with "Kavya Rai — Full-stack Developer" (or similar)
    - _Requirements: 7.1, 7.2_

- [x] 11. Final Checkpoint
  - Ensure all tests pass, ask the user if questions arise.
  - Verify end-to-end: create complaint with images → view in gallery → open lightbox → delete image

## Task Dependency Graph

```json
{
  "waves": [
    { "wave": 1, "tasks": ["1"] },
    { "wave": 2, "tasks": ["2"] },
    { "wave": 3, "tasks": ["3"] },
    { "wave": 4, "tasks": ["4"] },
    { "wave": 5, "tasks": ["5"] },
    { "wave": 6, "tasks": ["6", "7"] },
    { "wave": 7, "tasks": ["8"] },
    { "wave": 8, "tasks": ["9"] },
    { "wave": 9, "tasks": ["10"] },
    { "wave": 10, "tasks": ["11"] }
  ]
}
```

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- The `ComplaintImage` model, `ComplaintImageRead` schema, and frontend `ComplaintImage` interface already exist — do NOT recreate them
- The `UPLOAD_DIR` setting already exists in `backend/app/core/config.py`
- The StaticFiles mount is already in `main.py` but commented out — just uncomment it
- Follow existing code patterns exactly: static methods on repository/service classes, React Query hooks with toast notifications
- Each task references specific requirements for traceability
