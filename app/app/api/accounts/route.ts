import { createAuthenticatedRoute } from "@/lib/api-wrapper";

export const { GET, POST } = createAuthenticatedRoute("/api/v1/accounts");
