$home = '/home/pgf2xcsto0v0';
$out  = array(
	'time' => current_time( 'mysql' ),
	'abspath' => defined( 'ABSPATH' ) ? ABSPATH : null,
	'uploads' => wp_upload_dir(),
);

// Resolve realpaths around this install
$candidates = array(
	$home,
	dirname( rtrim( ABSPATH, '/\\' ) ),
	dirname( dirname( rtrim( ABSPATH, '/\\' ) ) ),
	rtrim( ABSPATH, '/\\' ) . '/../',
);

$seen = array();
$out['listings'] = array();
foreach ( $candidates as $dir ) {
	$real = realpath( $dir );
	if ( ! $real || isset( $seen[ $real ] ) ) {
		continue;
	}
	$seen[ $real ] = true;
	$items = array();
	if ( is_dir( $real ) && is_readable( $real ) ) {
		foreach ( scandir( $real ) as $f ) {
			if ( $f === '.' || $f === '..' ) {
				continue;
			}
			$p = $real . '/' . $f;
			$items[] = array(
				'name'  => $f,
				'dir'   => is_dir( $p ),
				'link'  => is_link( $p ) ? ( readlink( $p ) ?: true ) : false,
				'has_wp'=> is_dir( $p ) && file_exists( $p . '/wp-config.php' ),
			);
		}
	}
	$out['listings'][ $real ] = $items;
}

// Search likely shop paths
$guesses = array(
	$home . '/sunviksteels.shop',
	$home . '/public_html/sunviksteels.shop',
	$home . '/public_html/shop',
	$home . '/domains/sunviksteels.shop/public_html',
	$home . '/public_html/public_html',
	dirname( rtrim( ABSPATH, '/\\' ) ) . '/sunviksteels.shop',
	dirname( rtrim( ABSPATH, '/\\' ) ) . '/shop',
);
$out['guesses'] = array();
foreach ( $guesses as $g ) {
	$out['guesses'][ $g ] = array(
		'exists' => file_exists( $g ),
		'is_dir' => is_dir( $g ),
		'wp'     => file_exists( $g . '/wp-config.php' ) || file_exists( $g . '/public_html/wp-config.php' ),
	);
}

// Walk home one level deeper for any wp-config named shop-ish
$out['wp_installs'] = array();
if ( is_dir( $home ) && is_readable( $home ) ) {
	$stack = array( $home );
	$depth = 0;
	while ( $stack && $depth < 80 ) {
		$dir = array_shift( $stack );
		$depth++;
		$files = @scandir( $dir );
		if ( ! $files ) {
			continue;
		}
		$has_config = in_array( 'wp-config.php', $files, true );
		if ( $has_config ) {
			$out['wp_installs'][] = $dir;
		}
		// recurse limited
		$level = substr_count( str_replace( $home, '', $dir ), '/' );
		if ( $level >= 3 ) {
			continue;
		}
		foreach ( $files as $f ) {
			if ( $f === '.' || $f === '..' ) {
				continue;
			}
			$p = $dir . '/' . $f;
			if ( is_dir( $p ) && ! is_link( $p ) ) {
				// skip heavy dirs
				if ( in_array( $f, array( 'mail', 'etc', 'tmp', 'logs', 'ssl', 'cache', 'node_modules', '.trash' ), true ) ) {
					continue;
				}
				$stack[] = $p;
			}
		}
	}
}

$uploads = wp_upload_dir();
$path = trailingslashit( $uploads['basedir'] ) . 'sunvik-cpanel-scan-v1.json';
file_put_contents( $path, wp_json_encode( $out, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES ) );
