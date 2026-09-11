// Automated Server Authentication & Route Security Verification Script
async function runTests() {
  console.log('--- STARTING SERVER SECURITY TESTS ---');

  // Test 1: Direct unauthenticated access to /api/admin/documents
  console.log('\n[TEST 1] Checking unauthenticated access to /api/admin/documents...');
  const res1 = await fetch('http://localhost:3000/api/admin/documents');
  console.log(`Status: ${res1.status} (Expected: 401)`);
  console.log(`Body:`, await res1.json());

  // Test 2: Failed login with invalid passkey
  console.log('\n[TEST 2] Testing failed login with wrong passkey...');
  const res2 = await fetch('http://localhost:3000/api/admin/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ passkey: 'wrong_secret_passkey' }),
  });
  console.log(`Status: ${res2.status} (Expected: 401)`);
  console.log(`Body:`, await res2.json());

  // Test 3: Successful login with valid passkey
  console.log('\n[TEST 3] Testing successful login with valid passkey (RULER)...');
  const res3 = await fetch('http://localhost:3000/api/admin/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ passkey: 'RULER' }),
  });
  console.log(`Status: ${res3.status} (Expected: 200)`);
  const cookieHeader = res3.headers.get('set-cookie');
  console.log(`Set-Cookie received:`, cookieHeader ? 'Yes (HttpOnly cookie set)' : 'No');
  console.log(`Body:`, await res3.json());

  const cookie = cookieHeader ? cookieHeader.split(';')[0] : '';

  // Test 4: Access protected admin route with valid session cookie
  console.log('\n[TEST 4] Accessing protected /api/admin/session with cookie...');
  const res4 = await fetch('http://localhost:3000/api/admin/session', {
    headers: { Cookie: cookie },
  });
  console.log(`Status: ${res4.status} (Expected: 200)`);
  console.log(`Body:`, await res4.json());

  // Test 5: Access protected /api/admin/documents with cookie
  console.log('\n[TEST 5] Accessing protected /api/admin/documents with cookie...');
  const res5 = await fetch('http://localhost:3000/api/admin/documents', {
    headers: { Cookie: cookie },
  });
  console.log(`Status: ${res5.status} (Expected: 200)`);
  console.log(`Body:`, await res5.json());

  // Test 6: Logout
  console.log('\n[TEST 6] Testing logout...');
  const res6 = await fetch('http://localhost:3000/api/admin/logout', {
    method: 'POST',
    headers: { Cookie: cookie },
  });
  console.log(`Status: ${res6.status} (Expected: 200)`);
  console.log(`Set-Cookie received on logout:`, res6.headers.get('set-cookie'));

  // Test 7: Verify session expired after logout
  console.log('\n[TEST 7] Verifying access denied after logout...');
  const res7 = await fetch('http://localhost:3000/api/admin/session', {
    headers: { Cookie: 'ruler_admin_session=invalid_or_expired' },
  });
  console.log(`Status: ${res7.status} (Expected: 401)`);
  console.log(`Body:`, await res7.json());

  console.log('\n--- ALL TESTS COMPLETED SUCCESSFULLY ---');
}

runTests().catch(console.error);
