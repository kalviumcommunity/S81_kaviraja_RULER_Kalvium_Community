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
      details: 'Unauthorized attempt to invoke /api/admin/upload',
      success: false,
    });

    return NextResponse.json(
      {
        status: 'error',
        error: 'Unauthorized',
        message: 'Administrative authorization required to upload document files.',
      },
      { status: 401 }
    );
  }

  // 2. Forward multipart form data to backend
  try {
    const formData = await request.formData();
    const backendRes = await fetch(`${BACKEND_URL}/api/upload`, {
      method: 'POST',
      body: formData,
    });

    const data = await backendRes.json().catch(() => ({}));
    return NextResponse.json(data, { status: backendRes.status });
  } catch (err) {
    return NextResponse.json(
      {
        status: 'error',
        error: 'Backend Error',
        message: `Failed to forward document upload: ${err.message}`,
      },
      { status: 502 }
    );
  }
}
