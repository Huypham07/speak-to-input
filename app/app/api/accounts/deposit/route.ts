import { NextRequest, NextResponse } from "next/server";
import { authenticatedFetch } from "@/lib/api-wrapper";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { account_id, amount, note } = body;

    // Call backend deposit endpoint
    const response = await authenticatedFetch(request, `/api/v1/accounts/${account_id}/deposit`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        amount,
        note,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json({ error: data.detail || "Deposit failed" }, { status: response.status });
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("Deposit API error:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
