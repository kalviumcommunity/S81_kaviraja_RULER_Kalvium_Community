import { NextResponse } from 'next/server';
import { verifySessionToken, getCookieOptions } from '../../../../lib/auth-server';

const BACKEND_URL = process.env.BACKEND_INTERNAL_URL || 'http://127.0.0.1:8000';

export async function GET(request) {
  // 1. Verify Admin Session Cookie
  const cookieOpts = getCookieOptions();
  const sessionCookie = request.cookies.get(cookieOpts.name)?.value;
  const session = verifySessionToken(sessionCookie);

  if (!session) {
    return NextResponse.json(
      { status: 'error', error: 'Unauthorized', message: 'Admin authentication required.' },
      { status: 401 }
    );
  }

  try {
    const backendRes = await fetch(`${BACKEND_URL}/api/feedback?limit=100`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      cache: 'no-store',
    });

    if (!backendRes.ok) {
      return NextResponse.json({ status: 'success', total: 0, feedbacks: [] });
    }

    const data = await backendRes.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Admin feedback fetch error:', error);
    return NextResponse.json(
      { status: 'error', message: error.message },
      { status: 500 }
    );
  }
}
