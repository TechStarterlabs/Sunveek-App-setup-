delete_post_meta( 621, '_elementor_css' );
delete_post_meta( 621, '_elementor_element_cache' );
if ( class_exists( '\Elementor\Core\Files\CSS\Post' ) ) {
	try {
		$css = new \Elementor\Core\Files\CSS\Post( 621 );
		$css->update();
	} catch ( \Throwable $e ) {
		// ignore
	}
}
$uploads = wp_upload_dir();
file_put_contents( trailingslashit( $uploads['basedir'] ) . 'sunvik-css-regen.json', wp_json_encode( array( 'ok' => true ) ) );
