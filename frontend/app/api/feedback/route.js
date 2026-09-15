import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_INTERNAL_URL || 'http://127.0.0.1:8000';

export async function POST(request) {
  try {
    const body = await request.json().catch(() => ({}));

    // Forward feedback to FastAPI backend -> MongoDB
    const backendRes = await fetch(`${BACKEND_URL}/api/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!backendRes.ok) {
      const errText = await backendRes.text().catch(() => '');
      return NextResponse.json(
        { status: 'error', message: `Backend error: ${errText}` },
        { status: backendRes.status }
      );
    }

    const data = await backendRes.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Feedback submission proxy error:', error);
    return NextResponse.json(
      { status: 'error', message: error.message },
      { status: 500 }
    );
  }
}

export async function GET(request) {
  try {
    const backendRes = await fetch(`${BACKEND_URL}/api/feedback?limit=100`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      cache: 'no-store',
    });

    if (!backendRes.ok) {
      return NextResponse.json({ status: 'success', feedbacks: [] });
    }

    const data = await backendRes.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ status: 'error', message: error.message }, { status: 500 });
  }
}
