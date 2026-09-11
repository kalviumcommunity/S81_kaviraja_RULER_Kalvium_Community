import { NextResponse } from 'next/server';

const SESSION_COOKIE_NAME = 'ruler_admin_session';

export function middleware(request) {
  const { pathname } = request.nextUrl;

  // 1. Allow public auth endpoints
  if (pathname === '/api/admin/login' || pathname === '/api/admin/logout') {
    return NextResponse.next();
  }

  // 2. Protect sensitive admin API endpoints
  if (pathname.startsWith('/api/admin/')) {
    const sessionCookie = request.cookies.get(SESSION_COOKIE_NAME);
    if (!sessionCookie?.value) {
      return NextResponse.json(
        {
          status: 'error',
          error: 'Unauthorized',
          message: 'Valid administrator session required.',
        },
        { status: 401 }
      );
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/api/admin/:path*'],
};
