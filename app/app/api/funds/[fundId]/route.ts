import { NextRequest, NextResponse } from "next/server";
import { authenticatedFetch } from "@/lib/api-wrapper";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ fundId: string }> }
) {
  try {
    const { fundId } = await params;
    const response = await authenticatedFetch(request, `/api/v1/funds/${fundId}`);
    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json({ error: data.detail || "Request failed" }, { status: response.status });
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("API route error:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ fundId: string }> }
) {
  try {
    const { fundId } = await params;
    const response = await authenticatedFetch(request, `/api/v1/funds/${fundId}`, {
      method: "DELETE",
    });

    if (response.status === 204) {
      return new NextResponse(null, { status: 204 });
    }

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json({ error: data.detail || "Request failed" }, { status: response.status });
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("API route error:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
