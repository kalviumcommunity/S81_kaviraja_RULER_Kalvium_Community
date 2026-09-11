import { NextResponse } from 'next/server';
import {
  SESSION_COOKIE_NAME,
  verifySessionToken,
  logSecurityEvent,
} from '../../../../lib/auth-server';

const BACKEND_URL = process.env.BACKEND_INTERNAL_URL || 'http://127.0.0.1:8000';

export async function POST(request) {
  const forwardedFor = request.headers.get('x-forwarded-for');
  const ip = forwardedFor ? forwardedFor.split(',')[0].trim() : '127.0.0.1';

  // 1. Verify Server-Side Session
  const cookie = request.cookies.get(SESSION_COOKIE_NAME);
  const session = verifySessionToken(cookie?.value);

  if (!session) {
    logSecurityEvent({
      event: 'UNAUTHORIZED_ADMIN_ACTION',
      ip,
      details: 'Unauthorized attempt to invoke /api/admin/upload-text',
      success: false,
    });

    return NextResponse.json(
      {
        status: 'error',
        error: 'Unauthorized',
        message: 'Administrative authorization required to ingest policy documents.',
      },
      { status: 401 }
    );
  }

  // 2. Forward authorized payload to backend
  try {
    const payload = await request.json();
    const backendRes = await fetch(`${BACKEND_URL}/api/upload-text`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const data = await backendRes.json().catch(() => ({}));
    return NextResponse.json(data, { status: backendRes.status });
  } catch (err) {
    return NextResponse.json(
      {
        status: 'error',
        error: 'Backend Error',
        message: `Failed to communicate with ingestion engine: ${err.message}`,
      },
      { status: 502 }
    );
  }
}
