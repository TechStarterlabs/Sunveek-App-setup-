$uploads = wp_upload_dir();
$base = trailingslashit( $uploads['basedir'] );
foreach ( array( 'sunvik-lead-email-verify-v1.json', 'sunvik-lead-email-setup-v1.json' ) as $f ) {
  $p = $base . $f;
  if ( file_exists( $p ) ) { @unlink( $p ); }
}
delete_option( 'sunvik_lead_email_setup_v1' );
