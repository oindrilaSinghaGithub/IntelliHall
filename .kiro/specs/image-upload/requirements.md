# Requirements Document

## Introduction

This feature adds image upload and management capabilities to the IntelliHall complaint management
system. Students can attach photographic evidence when raising complaints, and both students and
Hall Admins can view and manage these images. The backend stores images on disk with UUID filenames
and tracks metadata in the existing `complaint_images` table. The frontend provides drag-and-drop
upload, image previews, a responsive gallery, and a lightbox viewer.

The backend is FastAPI + SQLAlchemy async + PostgreSQL. The frontend is Next.js 14 with React Query,
Tailwind CSS, and shadcn/ui. All new code follows existing Repository → Service → Endpoint and
Service → Hook → Component patterns.

## Glossary

- **Image_Upload_Service**: The backend service layer responsible for file validation, storage, and database persistence of complaint images.
- **Image_Upload_Endpoint**: The FastAPI API endpoint that accepts multipart/form-data image uploads.
- **Image_Delete_Endpoint**: The FastAPI API endpoint that removes an image file and its database record.
- **Static_File_Server**: The FastAPI StaticFiles mount that serves uploaded images at the `/uploads` path.
- **ImageUploader_Component**: The frontend React component providing drag-and-drop and browse-based file selection with previews.
- **ImageGallery_Component**: The frontend React component displaying uploaded images in a responsive grid.
- **ImagePreviewModal_Component**: The frontend React component showing a full-size image in a lightbox overlay.
- **Complaint_Owner**: The student who created the complaint (identified by `created_by` field).
- **Hall_Admin**: A user with `role = hall_admin` who manages complaints within their assigned hall.

## Requirements

### Requirement 1: Image Upload API

**User Story:** As a student or hall admin, I want to upload images to a complaint, so that I can provide photographic evidence of maintenance issues.

#### Acceptance Criteria

1. WHEN a POST request with multipart/form-data is received at `/api/v1/complaints/{complaint_id}/images`, THE Image_Upload_Endpoint SHALL accept one or more image files and return a list of ComplaintImageRead objects with HTTP 201.
2. WHEN the authenticated user is the Complaint_Owner, THE Image_Upload_Endpoint SHALL allow the upload to proceed.
3. WHEN the authenticated user is a Hall_Admin whose hall matches the complaint's `hall_id`, THE Image_Upload_Endpoint SHALL allow the upload to proceed.
4. WHEN the authenticated user is neither the Complaint_Owner nor the appropriate Hall_Admin, THE Image_Upload_Endpoint SHALL return HTTP 403 with message "Not authorized to upload images to this complaint."
5. WHEN an uploaded file has an extension other than jpg, jpeg, png, or webp, THE Image_Upload_Service SHALL reject the request with HTTP 400 and message "Invalid file type. Allowed: jpg, jpeg, png, webp."
6. WHEN an uploaded file exceeds 5 megabytes in size, THE Image_Upload_Service SHALL reject the request with HTTP 400 and message "File size exceeds 5MB limit."
7. WHEN the total image count for the complaint would exceed 5 after the upload, THE Image_Upload_Service SHALL reject the request with HTTP 400 and message "Maximum 5 images per complaint. Currently {n} images attached."
8. WHEN all validations pass, THE Image_Upload_Service SHALL store each file under `uploads/complaints/` with a UUID4 filename preserving the original extension.
9. WHEN all validations pass, THE Image_Upload_Service SHALL create a `complaint_images` database record with `image_url` set to the relative path (e.g., `/uploads/complaints/{uuid}.png`) and `uploaded_at` set to the current UTC timestamp.

### Requirement 2: Image Deletion API

**User Story:** As a student or hall admin, I want to delete an image from a complaint, so that I can remove incorrect or outdated photos.

#### Acceptance Criteria

1. WHEN a DELETE request is received at `/api/v1/complaints/images/{image_id}`, THE Image_Delete_Endpoint SHALL remove the physical file from disk and delete the database record, returning HTTP 204.
2. WHEN the authenticated user is the Complaint_Owner of the image's parent complaint, THE Image_Delete_Endpoint SHALL allow the deletion.
3. WHEN the authenticated user is a Hall_Admin whose hall matches the parent complaint's `hall_id`, THE Image_Delete_Endpoint SHALL allow the deletion.
4. WHEN the authenticated user is neither the Complaint_Owner nor the appropriate Hall_Admin, THE Image_Delete_Endpoint SHALL return HTTP 403 with message "Not authorized to delete this image."
5. IF the image record does not exist in the database, THEN THE Image_Delete_Endpoint SHALL return HTTP 404 with message "Image not found."
6. IF the physical file does not exist on disk when deletion is requested, THEN THE Image_Delete_Endpoint SHALL still delete the database record and return HTTP 204 without raising an error.

### Requirement 3: Static File Serving

**User Story:** As a user viewing a complaint, I want images to be accessible via URL, so that the frontend can display them.

#### Acceptance Criteria

1. THE Static_File_Server SHALL serve files from the `uploads` directory at the `/uploads` URL path.
2. WHEN the application starts, THE Image_Upload_Service SHALL ensure the `uploads/complaints/` directory exists, creating it if necessary.

### Requirement 4: Frontend Image Upload in Complaint Form

**User Story:** As a student raising a complaint, I want to attach images via drag-and-drop or file browser, so that I can visually document the issue.

#### Acceptance Criteria

1. THE ImageUploader_Component SHALL provide a drag-and-drop zone and a browse button for selecting image files.
2. WHEN files are selected or dropped, THE ImageUploader_Component SHALL display thumbnail previews of each selected image.
3. WHEN a selected file has a type other than image/jpeg, image/png, or image/webp, THE ImageUploader_Component SHALL display an error message "Only JPG, PNG, and WebP images are allowed" and exclude the file.
4. WHEN a selected file exceeds 5 megabytes, THE ImageUploader_Component SHALL display an error message "File exceeds 5MB size limit" and exclude the file.
5. WHEN the user selects more than 5 images total, THE ImageUploader_Component SHALL display an error message "Maximum 5 images allowed" and prevent additional selection.
6. WHEN the user clicks a remove button on a thumbnail, THE ImageUploader_Component SHALL remove that image from the selection.
7. WHEN the complaint form is submitted with images selected, THE ImageUploader_Component SHALL upload images to the backend after the complaint is created, displaying a progress indicator during upload.
8. WHEN the upload completes successfully, THE ImageUploader_Component SHALL display a success toast notification.
9. IF the upload fails, THEN THE ImageUploader_Component SHALL display an error toast notification with the error message from the server.

### Requirement 5: Frontend Image Gallery on Complaint Detail

**User Story:** As a student or hall admin viewing a complaint, I want to see all attached images in a gallery, so that I can review the photographic evidence.

#### Acceptance Criteria

1. WHEN a complaint with images is displayed on the detail page, THE ImageGallery_Component SHALL render images in a responsive grid layout.
2. WHEN a user clicks on an image in the gallery, THE ImagePreviewModal_Component SHALL open showing the full-size image.
3. WHEN the lightbox is open, THE ImagePreviewModal_Component SHALL provide a close button and support closing via Escape key or clicking outside.
4. WHEN the authenticated user is the Complaint_Owner or the appropriate Hall_Admin, THE ImageGallery_Component SHALL display a delete button on each image.
5. WHEN the user clicks the delete button on an image, THE ImageGallery_Component SHALL prompt for confirmation before calling the delete API.
6. WHEN deletion succeeds, THE ImageGallery_Component SHALL remove the image from the display and show a success toast notification.

### Requirement 6: Frontend Service and Hook Layer

**User Story:** As a developer, I want dedicated service functions and React Query hooks for image operations, so that the code follows existing project patterns.

#### Acceptance Criteria

1. THE complaint service module SHALL export an `uploadComplaintImages` function that sends a multipart POST request to `/api/v1/complaints/{complaint_id}/images`.
2. THE complaint service module SHALL export a `deleteComplaintImage` function that sends a DELETE request to `/api/v1/complaints/images/{image_id}`.
3. THE `useUploadImages` hook SHALL use React Query's `useMutation`, invalidate the complaint detail query on success, and show toast notifications.
4. THE `useDeleteImage` hook SHALL use React Query's `useMutation`, invalidate the complaint detail query on success, and show toast notifications.

### Requirement 7: Documentation Update

**User Story:** As a project contributor, I want the README to reflect the new feature and correct contributor roles, so that the documentation stays current.

#### Acceptance Criteria

1. WHEN the feature is complete, THE README.md SHALL contain a section describing the Image Upload feature and its capabilities.
2. THE README.md SHALL replace "Kavya Rai — Frontend" with a role reflecting full-stack contribution (e.g., "Full-stack Developer").
