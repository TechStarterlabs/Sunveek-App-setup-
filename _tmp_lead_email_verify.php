/**
 * Verify current lead-email config + cleanup public report JSON.
 */
$out = array( 'time' => current_time( 'mysql' ) );

foreach ( array( 11835, 10265, 8468, 8431 ) as $fid ) {
	$post = get_post( $fid );
	$data = $post ? json_decode( $post->post_content, true ) : null;
	$n    = ( is_array( $data ) && isset( $data['settings']['notifications'] ) ) ? $data['settings']['notifications'] : null;
	$c    = ( is_array( $data ) && isset( $data['settings']['confirmations']['1'] ) ) ? $data['settings']['confirmations']['1'] : null;
	$out['wpforms'][ $fid ] = array(
		'title'               => $post ? $post->post_title : null,
		'notification_enable' => is_array( $data ) ? ( $data['settings']['notification_enable'] ?? null ) : null,
		'notifications'       => $n,
		'confirmation_type'   => is_array( $c ) ? ( $c['type'] ?? null ) : null,
		'redirect'            => is_array( $c ) ? ( $c['redirect'] ?? null ) : null,
	);
}

if ( class_exists( 'WPCF7_ContactForm' ) ) {
	foreach ( array( 227, 232 ) as $id ) {
		$cf = WPCF7_ContactForm::get_instance( $id );
		if ( ! $cf ) {
			continue;
		}
		$mail = $cf->prop( 'mail' );
		$out['cf7'][ $id ] = array(
			'title'     => $cf->title(),
			'recipient' => $mail['recipient'] ?? null,
			'subject'   => $mail['subject'] ?? null,
			'headers'   => $mail['additional_headers'] ?? null,
			'active'    => $mail['active'] ?? null,
		);
	}
}

$uploads = wp_upload_dir();
$base    = trailingslashit( $uploads['basedir'] );
foreach ( array( 'sunvik-lead-email-setup-v1.json', 'sunvik-wpforms-dump-v1.json', 'sunvik-wpforms-entries-v1.json' ) as $f ) {
	$p = $base . $f;
	if ( file_exists( $p ) ) {
		@unlink( $p );
		$out['cleaned'][] = $f;
	}
}

$path = $base . 'sunvik-lead-email-verify-v1.json';
file_put_contents( $path, wp_json_encode( $out, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES ) );
