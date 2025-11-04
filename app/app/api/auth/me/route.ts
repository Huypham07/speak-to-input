import { createAuthenticatedRoute } from "@/lib/api-wrapper";

// Dùng createAuthenticatedRoute vì chỉ cần forward request đơn giản
export const { GET } = createAuthenticatedRoute("/api/v1/auth/me");
