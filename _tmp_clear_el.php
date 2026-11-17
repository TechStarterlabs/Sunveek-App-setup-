$post_id = 621;
delete_post_meta( $post_id, '_elementor_css' );
delete_post_meta( $post_id, '_elementor_element_cache' );
if ( class_exists( '\Elementor\Plugin' ) ) {
	\Elementor\Plugin::$instance->files_manager->clear_cache();
}
// bump so front regenerates
update_post_meta( $post_id, '_elementor_version', '3.0.0' );
$uploads = wp_upload_dir();
file_put_contents(
	trailingslashit( $uploads['basedir'] ) . 'sunvik-el-clear.json',
	wp_json_encode( array( 'ok' => true, 'time' => current_time( 'mysql' ) ) )
);
