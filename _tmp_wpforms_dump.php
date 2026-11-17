delete_option( 'sunvik_wpforms_dump_done_v1' );

$out = array(
	'time' => current_time( 'mysql' ),
	'admin_email' => get_option( 'admin_email' ),
	'blogname' => get_option( 'blogname' ),
);

$post = get_post( 11835 );
if ( ! $post ) {
	$q = get_posts( array( 'post_type' => 'wpforms', 'post_status' => 'any', 'numberposts' => 50 ) );
	$out['wpforms_posts'] = array();
	foreach ( $q as $p ) {
		$out['wpforms_posts'][] = array( 'id' => $p->ID, 'title' => $p->post_title, 'status' => $p->post_status, 'len' => strlen( $p->post_content ) );
	}
	$out['error'] = 'post 11835 not found';
} else {
	$out['post'] = array(
		'id' => $post->ID,
		'type' => $post->post_type,
		'title' => $post->post_title,
		'status' => $post->post_status,
		'modified' => $post->post_modified,
	);
	$data = json_decode( $post->post_content, true );
	if ( ! is_array( $data ) ) {
		$out['decode_error'] = true;
		$out['raw_preview'] = substr( $post->post_content, 0, 500 );
	} else {
		$out['settings'] = isset( $data['settings'] ) ? $data['settings'] : null;
		$out['fields_summary'] = array();
		if ( ! empty( $data['fields'] ) && is_array( $data['fields'] ) ) {
			foreach ( $data['fields'] as $fid => $f ) {
				$out['fields_summary'][] = array(
					'id' => $fid,
					'type' => isset( $f['type'] ) ? $f['type'] : '',
					'label' => isset( $f['label'] ) ? $f['label'] : '',
				);
			}
		}
		$out['meta_keys'] = array_keys( $data );
	}
}

$all = get_posts( array( 'post_type' => 'wpforms', 'post_status' => 'any', 'numberposts' => 100 ) );
$out['all_forms'] = array();
foreach ( $all as $p ) {
	$d = json_decode( $p->post_content, true );
	$settings = ( is_array( $d ) && isset( $d['settings'] ) ) ? $d['settings'] : array();
	$out['all_forms'][] = array(
		'id' => $p->ID,
		'title' => $p->post_title,
		'notification_enable' => isset( $settings['notification_enable'] ) ? $settings['notification_enable'] : null,
		'notifications' => isset( $settings['notifications'] ) ? $settings['notifications'] : null,
		'confirmations' => isset( $settings['confirmations'] ) ? $settings['confirmations'] : null,
	);
}

$smtp = get_option( 'wp_mail_smtp' );
if ( is_array( $smtp ) ) {
	$safe = $smtp;
	array_walk_recursive( $safe, function ( &$v, $k ) {
		if ( is_string( $k ) && preg_match( '/pass|secret|key|token/i', $k ) ) {
			$v = is_string( $v ) && strlen( $v ) ? '[set:' . strlen( $v ) . ']' : $v;
		}
	} );
	$out['wp_mail_smtp'] = $safe;
} else {
	$out['wp_mail_smtp'] = $smtp;
}

global $wpdb;
$tables = $wpdb->get_col( 'SHOW TABLES' );
$out['wpforms_tables'] = array_values( array_filter( $tables, function( $t ) {
	return stripos( $t, 'wpforms' ) !== false;
} ) );

$uploads = wp_upload_dir();
$path = trailingslashit( $uploads['basedir'] ) . 'sunvik-wpforms-dump-v1.json';
file_put_contents( $path, wp_json_encode( $out, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES ) );
update_option( 'sunvik_wpforms_dump_done_v1', array( 'path' => $path, 'url' => trailingslashit( $uploads['baseurl'] ) . 'sunvik-wpforms-dump-v1.json' ), false );
