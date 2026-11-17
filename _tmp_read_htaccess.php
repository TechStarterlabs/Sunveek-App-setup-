
 = ABSPATH . '.htaccess';
 = array(
	'exists' => file_exists(  ),
	'writable' => is_writable(  ) || is_writable( ABSPATH ),
	'size' => file_exists(  ) ? filesize(  ) : 0,
	'content' => file_exists(  ) ? file_get_contents(  ) : null,
);
 = wp_upload_dir();
file_put_contents( trailingslashit( ['basedir'] ) . 'sunvik-htaccess-read.json', wp_json_encode(  ) );
