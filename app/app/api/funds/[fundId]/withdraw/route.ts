import { NextRequest, NextResponse } from "next/server";
import { authenticatedFetch } from "@/lib/api-wrapper";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ fundId: string }> }
) {
  try {
    const { fundId } = await params;
    const body = await request.json();

    const response = await authenticatedFetch(request, `/api/v1/funds/${fundId}/withdraw`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json({ error: data.detail || "Withdrawal failed" }, { status: response.status });
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("Withdrawal API error:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
