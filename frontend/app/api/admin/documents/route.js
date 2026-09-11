import { NextResponse } from 'next/server';
import {
  SESSION_COOKIE_NAME,
  verifySessionToken,
  logSecurityEvent,
} from '../../../../lib/auth-server';

const BACKEND_URL = process.env.BACKEND_INTERNAL_URL || 'http://127.0.0.1:8000';

export async function GET(request) {
  const forwardedFor = request.headers.get('x-forwarded-for');
  const ip = forwardedFor ? forwardedFor.split(',')[0].trim() : '127.0.0.1';

  // 1. Verify Server-Side Session
  const cookie = request.cookies.get(SESSION_COOKIE_NAME);
  const session = verifySessionToken(cookie?.value);

  if (!session) {
    logSecurityEvent({
      event: 'UNAUTHORIZED_ADMIN_ACTION',
      ip,
      details: 'Unauthorized attempt to inspect /api/admin/documents',
      success: false,
    });

    return NextResponse.json(
      {
        status: 'error',
        error: 'Unauthorized',
        message: 'Administrative authorization required to inspect document repository.',
      },
      { status: 401 }
    );
  }

  // 2. Fetch documents from backend
  try {
    const backendRes = await fetch(`${BACKEND_URL}/api/documents`);
    const data = await backendRes.json().catch(() => ({}));
    return NextResponse.json(data, { status: backendRes.status });
  } catch (err) {
    return NextResponse.json(
      {
        status: 'error',
        error: 'Backend Error',
        message: `Failed to fetch documents: ${err.message}`,
      },
      { status: 502 }
    );
  }
}
