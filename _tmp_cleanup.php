$uploads = wp_upload_dir();
$base = trailingslashit( $uploads['basedir'] );
foreach ( array( 'sunvik-wpforms-dump-v1.json', 'sunvik-wpforms-entries-v1.json' ) as $f ) {
	$path = $base . $f;
	if ( file_exists( $path ) ) { unlink( $path ); }
}
delete_option( 'sunvik_wpforms_dump_done_v1' );
