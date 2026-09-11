import { NextResponse } from 'next/server';
import {
  SESSION_COOKIE_NAME,
  verifySessionToken,
  logSecurityEvent,
} from '../../../../lib/auth-server';

export async function GET(request) {
  const forwardedFor = request.headers.get('x-forwarded-for');
  const ip = forwardedFor ? forwardedFor.split(',')[0].trim() : '127.0.0.1';

  const cookie = request.cookies.get(SESSION_COOKIE_NAME);
  const token = cookie?.value;

  if (!token) {
    return NextResponse.json(
      {
        authenticated: false,
        error: 'Unauthorized',
        message: 'No active admin session found.',
      },
      { status: 401 }
    );
  }

  const session = verifySessionToken(token);

  if (!session) {
    logSecurityEvent({
      event: 'UNAUTHORIZED_ACCESS_ATTEMPT',
      ip,
      details: 'Invalid or expired session token provided for /api/admin/session',
      success: false,
    });

    const response = NextResponse.json(
      {
        authenticated: false,
        error: 'Unauthorized',
        message: 'Admin session is invalid or expired. Please re-authenticate.',
      },
      { status: 401 }
    );

    // Clear stale cookie
    response.cookies.set({
      name: SESSION_COOKIE_NAME,
      value: '',
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      path: '/',
      maxAge: 0,
    });

    return response;
  }

  return NextResponse.json({
    authenticated: true,
    user: {
      role: 'Administrator',
      name: session.name || 'Chief Compliance Administrator',
      adminId: session.adminId,
    },
  });
}
