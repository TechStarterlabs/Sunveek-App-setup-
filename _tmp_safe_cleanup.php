$post_id = 621;
delete_post_meta( $post_id, '_elementor_css' );
delete_post_meta( $post_id, '_elementor_element_cache' );
// Ensure deadly snippet stays off
global $wpdb;
$wpdb->update( $wpdb->prefix . 'snippets', array( 'active' => 0 ), array( 'id' => 13 ) );
$wpdb->query( "UPDATE {$wpdb->prefix}snippets SET active = 0 WHERE name LIKE 'TEMP%'" );
$uploads = wp_upload_dir();
file_put_contents(
	trailingslashit( $uploads['basedir'] ) . 'sunvik-safe-cleanup.json',
	wp_json_encode( array( 'ok' => true, 'time' => current_time( 'mysql' ) ) )
);
