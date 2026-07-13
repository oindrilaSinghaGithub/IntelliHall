import { BACKEND_ORIGIN } from "@/constants";

/**
 * Resolve a complaint image URL for use in <img src>.
 * Relative paths from the API (e.g. /uploads/...) are prefixed with the backend origin.
 */
export function resolveImageUrl(imageUrl: string): string {
  if (imageUrl.startsWith("http://") || imageUrl.startsWith("https://")) {
    return imageUrl;
  }
  return `${BACKEND_ORIGIN}${imageUrl.startsWith("/") ? imageUrl : `/${imageUrl}`}`;
}
