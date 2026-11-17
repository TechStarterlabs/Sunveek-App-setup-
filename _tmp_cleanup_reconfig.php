$uploads = wp_upload_dir();
$base = trailingslashit( $uploads['basedir'] );
foreach ( array( 'sunvik-lead-reconfig-v2.json', 'sunvik-final-check-v1.json' ) as $f ) {
  $p = $base . $f; if ( file_exists( $p ) ) { @unlink( $p ); }
}
