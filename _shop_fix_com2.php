$com_config = '/home/pgf2xcsto0v0/public_html/wp-config.php';
$report = array( 'time' => date( 'c' ) );

if ( ! file_exists( $com_config ) ) {
	$report['error'] = 'com config missing';
} else {
	$cfg = file_get_contents( $com_config );
	preg_match( '/define\s*\(\s*[\'"]DB_NAME[\'"]\s*,\s*[\'"]([^\'"]+)[\'"]\s*\)/', $cfg, $m_name );
	preg_match( '/define\s*\(\s*[\'"]DB_USER[\'"]\s*,\s*[\'"]([^\'"]+)[\'"]\s*\)/', $cfg, $m_user );
	preg_match( '/define\s*\(\s*[\'"]DB_PASSWORD[\'"]\s*,\s*[\'"]([^\'"]*)[\'"]\s*\)/', $cfg, $m_pass );
	preg_match( '/define\s*\(\s*[\'"]DB_HOST[\'"]\s*,\s*[\'"]([^\'"]+)[\'"]\s*\)/', $cfg, $m_host );
	preg_match( '/\$table_prefix\s*=\s*[\'"]([^\'"]+)[\'"]\s*;/', $cfg, $m_prefix );

	$report['db_name'] = isset( $m_name[1] ) ? $m_name[1] : null;
	$report['db_user'] = isset( $m_user[1] ) ? $m_user[1] : null;
	$report['db_host'] = isset( $m_host[1] ) ? $m_host[1] : null;
	$report['prefix']  = isset( $m_prefix[1] ) ? $m_prefix[1] : null;
	$report['pass_len'] = isset( $m_pass[1] ) ? strlen( $m_pass[1] ) : 0;

	if ( empty( $m_name[1] ) || empty( $m_user[1] ) ) {
		$report['error'] = 'failed to parse wp-config';
	} else {
		$mysqli = @new mysqli( $m_host[1], $m_user[1], $m_pass[1], $m_name[1] );
		if ( $mysqli->connect_errno ) {
			$report['error'] = $mysqli->connect_error;
		} else {
			$prefix = $m_prefix[1];
			$table  = $prefix . 'snippets';
			$mysqli->query( "UPDATE `{$table}` SET active = 0 WHERE id = 13" );
			$report['affected_13'] = $mysqli->affected_rows;
			$mysqli->query( "UPDATE `{$table}` SET active = 0 WHERE name LIKE 'TEMP%'" );
			$report['temps_off'] = $mysqli->affected_rows;
			// list active snippets remaining
			$res = $mysqli->query( "SELECT id, name, active FROM `{$table}` WHERE active = 1" );
			$report['still_active'] = array();
			if ( $res ) {
				while ( $row = $res->fetch_assoc() ) {
					$report['still_active'][] = $row;
				}
			}
			$mysqli->close();
		}
	}
}

$plugin     = '/home/pgf2xcsto0v0/public_html/wp-content/plugins/code-snippets';
$plugin_off = $plugin . '-off';
if ( is_dir( $plugin_off ) && ! is_dir( $plugin ) ) {
	$report['restore_plugin'] = rename( $plugin_off, $plugin );
} elseif ( is_dir( $plugin ) ) {
	$report['restore_plugin'] = 'already_on';
} else {
	$report['restore_plugin'] = 'missing_both';
}

@file_put_contents(
	'/home/pgf2xcsto0v0/public_html/sunviksteels.shop/wp-content/uploads/sunvik-com-fix2.json',
	json_encode( $report, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES )
);
