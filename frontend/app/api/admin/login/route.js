import { NextResponse } from 'next/server';
import {
  checkRateLimit,
  recordFailedAttempt,
  resetRateLimit,
  verifyAdminPasskey,
  createSessionToken,
  logSecurityEvent,
  getCookieOptions,
} from '../../../../lib/auth-server';

export async function POST(request) {
  // Extract client IP for rate limiting and auditing
  const forwardedFor = request.headers.get('x-forwarded-for');
  const ip = forwardedFor ? forwardedFor.split(',')[0].trim() : '127.0.0.1';

  // 1. Check Rate Limit & Brute-Force Protection
  const rateLimit = checkRateLimit(ip);
  if (!rateLimit.allowed) {
    logSecurityEvent({
      event: 'RATE_LIMITED',
      ip,
      details: `Login blocked due to brute-force threshold. Retry after ${rateLimit.retryAfterMinutes}m`,
      success: false,
    });

    return NextResponse.json(
      {
        status: 'error',
        error: 'Too Many Requests',
        message: rateLimit.message,
        retryAfterMinutes: rateLimit.retryAfterMinutes,
      },
      { status: 429 }
    );
  }

  try {
    const body = await request.json().catch(() => ({}));
    const { passkey } = body;

    // 2. Validate input presence
    if (!passkey || typeof passkey !== 'string') {
      recordFailedAttempt(ip);
      logSecurityEvent({
        event: 'LOGIN_FAILED',
        ip,
        details: 'Missing or malformed passkey payload',
        success: false,
      });

      return NextResponse.json(
        {
          status: 'error',
          error: 'Authentication Error',
          message: 'Admin passkey is required.',
        },
        { status: 400 }
      );
    }

    // 3. Timing-Safe Passkey Verification
    const isAuthorized = verifyAdminPasskey(passkey);

    if (!isAuthorized) {
      recordFailedAttempt(ip);
      const remainingAttempts = checkRateLimit(ip).remaining;

      logSecurityEvent({
        event: 'LOGIN_FAILED',
        ip,
        details: `Invalid passkey supplied. Remaining attempts before lockout: ${remainingAttempts}`,
        success: false,
      });

      return NextResponse.json(
        {
          status: 'error',
          error: 'Unauthorized',
          message: 'Invalid administrative passkey. Access denied.',
        },
        { status: 401 }
      );
    }

    // 4. Successful Authentication
    resetRateLimit(ip);
    const sessionToken = createSessionToken({
      adminId: 'ruler_chief_compliance_admin',
      role: 'Administrator',
      name: 'Chief Compliance Administrator',
    });

    logSecurityEvent({
      event: 'LOGIN_SUCCESS',
      ip,
      details: 'Administrator session established successfully',
      success: true,
    });

    // 5. Build Response with HttpOnly Secure Cookie
    const cookieOpts = getCookieOptions();
    const response = NextResponse.json({
      status: 'success',
      message: 'Admin session authorized successfully.',
      user: {
        role: 'Administrator',
        name: 'Chief Compliance Administrator',
      },
    });

    response.cookies.set({
      name: cookieOpts.name,
      value: sessionToken,
      httpOnly: cookieOpts.httpOnly,
      secure: cookieOpts.secure,
      sameSite: cookieOpts.sameSite,
      path: cookieOpts.path,
      maxAge: cookieOpts.maxAge,
    });

    return response;
  } catch (error) {
    logSecurityEvent({
      event: 'LOGIN_ERROR',
      ip,
      details: `Internal authentication exception: ${error.message}`,
      success: false,
    });

    return NextResponse.json(
      {
        status: 'error',
        error: 'Internal Server Error',
        message: 'An error occurred during authentication processing.',
      },
      { status: 500 }
    );
  }
}
