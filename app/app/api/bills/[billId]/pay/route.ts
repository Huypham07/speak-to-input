import { NextRequest, NextResponse } from "next/server";
import { authenticatedFetch } from "@/lib/api-wrapper";

export async function POST(request: NextRequest, { params }: { params: Promise<{ billId: string }> }) {
  try {
    const { billId } = await params;
    const url = new URL(request.url);
    const fromAccountId = url.searchParams.get("from_account_id");

    // Build backend endpoint
    let endpoint = `/api/v1/bills/${billId}/pay`;
    if (fromAccountId) {
      endpoint += `?from_account_id=${fromAccountId}`;
    }

    const response = await authenticatedFetch(request, endpoint, {
      method: "POST",
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { error: data.detail || data.message || "Failed to pay bill" },
        { status: response.status }
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("API route error:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
