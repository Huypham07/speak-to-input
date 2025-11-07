import { createAuthenticatedRoute } from "@/lib/api-wrapper";

export const { GET } = createAuthenticatedRoute("/api/v1/accounts/others");
