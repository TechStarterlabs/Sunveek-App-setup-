/**
 * Sunvik — Security headers (audit remediation)
 * Safe defaults for Elementor / GTM / WhatsApp / fonts stack.
 * CSP is intentionally permissive so scripts/styles are not broken.
 */
add_action( 'send_headers', function () {
	if ( headers_sent() ) {
		return;
	}

	header( 'X-Content-Type-Options: nosniff', true );
	header( 'X-Frame-Options: SAMEORIGIN', true );
	header( 'Referrer-Policy: strict-origin-when-cross-origin', true );
	header( 'Strict-Transport-Security: max-age=31536000; includeSubDomains', true );

	// Permissive CSP: header present for scanners; allows Elementor inline + third parties over HTTPS.
	$csp = implode(
		'; ',
		array(
			"default-src 'self' https: data: blob: 'unsafe-inline' 'unsafe-eval'",
			"img-src 'self' https: data: blob:",
			"font-src 'self' https: data:",
			"frame-ancestors 'self'",
			'upgrade-insecure-requests',
		)
	);
	header( 'Content-Security-Policy: ' . $csp, true );
}, 1 );
