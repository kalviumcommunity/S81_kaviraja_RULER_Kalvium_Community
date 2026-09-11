/**
 * Server-Side Authentication, Cryptographic Verification,
 * Session Management, Rate Limiting, and Security Auditing
 */

import crypto from 'crypto';

// Server-side Environment Variables (Never expose via NEXT_PUBLIC_)
const ADMIN_PASSKEY = process.env.ADMIN_PASSKEY || 'RULER';
const SESSION_SECRET = process.env.SESSION_SECRET || 'ruler_session_hmac_secret_key_banking_reg_99812';
const SESSION_COOKIE_NAME = 'ruler_admin_session';
const SESSION_DURATION_SECONDS = 60 * 60 * 8; // 8 hours

// -------------------------------------------------------------
// 1. IN-MEMORY SLIDING-WINDOW RATE LIMITER & BRUTE FORCE PROTECTION
// -------------------------------------------------------------
const MAX_ATTEMPTS = 5;
const WINDOW_MS = 15 * 60 * 1000; // 15 minutes
const loginAttempts = new Map(); // ip -> { count: number, firstAttempt: number, lockedUntil: number }

export function checkRateLimit(ip = 'unknown') {
  const now = Date.now();
  const record = loginAttempts.get(ip);

  if (!record) {
    return { allowed: true, remaining: MAX_ATTEMPTS };
  }

  // Check if currently locked
  if (record.lockedUntil && now < record.lockedUntil) {
    const minutesLeft = Math.ceil((record.lockedUntil - now) / 60000);
    return {
      allowed: false,
      remaining: 0,
      retryAfterMinutes: minutesLeft,
      message: `Too many failed login attempts. Access locked for ${minutesLeft} minute(s).`,
    };
  }

  // Reset window if expired
  if (now - record.firstAttempt > WINDOW_MS) {
    loginAttempts.delete(ip);
    return { allowed: true, remaining: MAX_ATTEMPTS };
  }

  if (record.count >= MAX_ATTEMPTS) {
    record.lockedUntil = now + WINDOW_MS;
    const minutesLeft = Math.ceil(WINDOW_MS / 60000);
    return {
      allowed: false,
      remaining: 0,
      retryAfterMinutes: minutesLeft,
      message: `Too many failed login attempts. Access locked for ${minutesLeft} minute(s).`,
    };
  }

  return { allowed: true, remaining: MAX_ATTEMPTS - record.count };
}

export function recordFailedAttempt(ip = 'unknown') {
  const now = Date.now();
  const record = loginAttempts.get(ip);

  if (!record || now - record.firstAttempt > WINDOW_MS) {
    loginAttempts.set(ip, { count: 1, firstAttempt: now, lockedUntil: null });
  } else {
    record.count += 1;
    if (record.count >= MAX_ATTEMPTS) {
      record.lockedUntil = now + WINDOW_MS;
    }
  }
}

export function resetRateLimit(ip = 'unknown') {
  loginAttempts.delete(ip);
}

// -------------------------------------------------------------
// 2. TIMING-SAFE PASSKEY VERIFICATION
// -------------------------------------------------------------
export function verifyAdminPasskey(providedPasskey) {
  if (typeof providedPasskey !== 'string' || !providedPasskey) {
    return false;
  }

  const targetKey = ADMIN_PASSKEY.trim();
  const inputKey = providedPasskey.trim();

  // Hash both inputs using SHA-256 to ensure identical fixed buffer lengths
  const hashTarget = crypto.createHash('sha256').update(targetKey, 'utf8').digest();
  const hashInput = crypto.createHash('sha256').update(inputKey, 'utf8').digest();

  // Constant-time comparison to prevent timing attacks
  return crypto.timingSafeEqual(hashTarget, hashInput);
}

// -------------------------------------------------------------
// 3. CRYPTOGRAPHIC SIGNED SESSION TOKENS (HMAC-SHA256)
// -------------------------------------------------------------
export function createSessionToken(payload = {}) {
  const header = { alg: 'HS256', typ: 'JWT' };
  const now = Math.floor(Date.now() / 1000);
  const data = {
    ...payload,
    role: 'Administrator',
    iat: now,
    exp: now + SESSION_DURATION_SECONDS,
    jti: crypto.randomBytes(16).toString('hex'),
  };

  const encodedHeader = Buffer.from(JSON.stringify(header)).toString('base64url');
  const encodedPayload = Buffer.from(JSON.stringify(data)).toString('base64url');
  const signatureInput = `${encodedHeader}.${encodedPayload}`;

  const signature = crypto
    .createHmac('sha256', SESSION_SECRET)
    .update(signatureInput)
    .digest('base64url');

  return `${signatureInput}.${signature}`;
}

export function verifySessionToken(token) {
  if (!token || typeof token !== 'string') return null;

  const parts = token.split('.');
  if (parts.length !== 3) return null;

  const [encodedHeader, encodedPayload, providedSignature] = parts;
  const signatureInput = `${encodedHeader}.${encodedPayload}`;

  const expectedSignature = crypto
    .createHmac('sha256', SESSION_SECRET)
    .update(signatureInput)
    .digest('base64url');

  // Verify signature with constant-time equality
  const expectedBuf = Buffer.from(expectedSignature);
  const providedBuf = Buffer.from(providedSignature);

  if (expectedBuf.length !== providedBuf.length || !crypto.timingSafeEqual(expectedBuf, providedBuf)) {
    return null;
  }

  try {
    const payload = JSON.parse(Buffer.from(encodedPayload, 'base64url').toString('utf8'));
    const now = Math.floor(Date.now() / 1000);

    // Check expiration
    if (payload.exp && payload.exp < now) {
      return null;
    }

    if (payload.role !== 'Administrator') {
      return null;
    }

    return payload;
  } catch (e) {
    return null;
  }
}

// -------------------------------------------------------------
// 4. SECURITY AUDIT LOGGING
// -------------------------------------------------------------
export function logSecurityEvent({ event, ip = 'unknown', details = '', success = true }) {
  const timestamp = new Date().toISOString();
  const logEntry = {
    timestamp,
    event,
    ip,
    success,
    details,
  };

  const formatted = `[SECURITY AUDIT] [${timestamp}] [${event}] [IP: ${ip}] [Success: ${success}] - ${details}`;
  if (success) {
    console.log(formatted);
  } else {
    console.warn(formatted);
  }

  return logEntry;
}

// -------------------------------------------------------------
// 5. COOKIE CONFIGURATION HELPER
// -------------------------------------------------------------
export function getCookieOptions() {
  const isProduction = process.env.NODE_ENV === 'production';
  return {
    name: SESSION_COOKIE_NAME,
    httpOnly: true,
    secure: isProduction,
    sameSite: 'lax',
    path: '/',
    maxAge: SESSION_DURATION_SECONDS,
  };
}

export { SESSION_COOKIE_NAME, SESSION_DURATION_SECONDS };
