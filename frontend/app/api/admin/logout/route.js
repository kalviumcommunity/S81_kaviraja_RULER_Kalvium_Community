import { NextResponse } from 'next/server';
import {
  SESSION_COOKIE_NAME,
  logSecurityEvent,
} from '../../../../lib/auth-server';

export async function POST(request) {
  const forwardedFor = request.headers.get('x-forwarded-for');
  const ip = forwardedFor ? forwardedFor.split(',')[0].trim() : '127.0.0.1';

  logSecurityEvent({
    event: 'LOGOUT',
    ip,
    details: 'Administrator session invalidated by user',
    success: true,
  });

  const response = NextResponse.json({
    status: 'success',
    message: 'Admin session terminated successfully.',
  });

  // Expire the session cookie immediately
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
