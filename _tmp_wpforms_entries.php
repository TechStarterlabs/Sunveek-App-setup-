delete_option( 'sunvik_wpforms_dump_done_v1' );

global $wpdb;
$out = array( 'time' => current_time( 'mysql' ) );

$forms = array( 11835, 10265, 8468, 8431 );
$out['entry_counts'] = array();
foreach ( $forms as $fid ) {
	$count = (int) $wpdb->get_var( $wpdb->prepare(
		"SELECT COUNT(*) FROM {$wpdb->prefix}wpforms_entries WHERE form_id = %d",
		$fid
	) );
	$recent = $wpdb->get_results( $wpdb->prepare(
		"SELECT entry_id, status, date, fields FROM {$wpdb->prefix}wpforms_entries WHERE form_id = %d ORDER BY entry_id DESC LIMIT 5",
		$fid
	), ARRAY_A );
	$safe_recent = array();
	foreach ( (array) $recent as $row ) {
		$fields = json_decode( $row['fields'], true );
		$summary = array();
		if ( is_array( $fields ) ) {
			foreach ( $fields as $f ) {
				$summary[] = array(
					'name' => isset( $f['name'] ) ? $f['name'] : '',
					'value' => isset( $f['value'] ) ? substr( (string) $f['value'], 0, 80 ) : '',
				);
			}
		}
		$safe_recent[] = array(
			'entry_id' => $row['entry_id'],
			'status' => $row['status'],
			'date' => $row['date'],
			'fields' => $summary,
		);
	}
	$out['entry_counts'][ $fid ] = array( 'count' => $count, 'recent' => $safe_recent );
}

// WP Mail SMTP debug log option if any
$out['wp_mail_smtp_debug'] = get_option( 'wp_mail_smtp_logs' ) ? 'has_logs_option' : 'no_logs_option';
$out['wp_mail_smtp_migration'] = get_option( 'wp_mail_smtp_debug_events' );

// Check for custom redirects in options / active snippets mentioning whatsapp+wpforms
$snippets = get_posts( array( 'post_type' => 'code_snippet', 'post_status' => 'any', 'numberposts' => 50 ) );
// Code Snippets may use custom table
$table = $wpdb->prefix . 'snippets';
$out['active_snippet_hits'] = array();
if ( $wpdb->get_var( $wpdb->prepare( 'SHOW TABLES LIKE %s', $table ) ) === $table ) {
	$rows = $wpdb->get_results( "SELECT id, name, active, code FROM {$table} WHERE active = 1", ARRAY_A );
	foreach ( (array) $rows as $r ) {
		$code = (string) $r['code'];
		if ( preg_match( '/whatsapp|wpforms|wa\.me|mail\(/i', $code ) ) {
			$out['active_snippet_hits'][] = array(
				'id' => $r['id'],
				'name' => $r['name'],
				'preview' => substr( $code, 0, 300 ),
			);
		}
	}
}

$uploads = wp_upload_dir();
$path = trailingslashit( $uploads['basedir'] ) . 'sunvik-wpforms-entries-v1.json';
file_put_contents( $path, wp_json_encode( $out, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES ) );
