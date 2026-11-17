/**
 * Ensure shop SMTP uses SSL 465 (more reliable on GoDaddy) and fire a shop-side test if possible.
 */
$report = array( 'time' => current_time( 'mysql' ) );

$cfg = file_get_contents( '/home/pgf2xcsto0v0/public_html/sunviksteels.shop/wp-config.php' );
preg_match( "/define\s*\(\s*'DB_NAME'\s*,\s*'([^']+)'\s*\)/", $cfg, $m_name );
preg_match( "/define\s*\(\s*'DB_USER'\s*,\s*'([^']+)'\s*\)/", $cfg, $m_user );
preg_match( "/define\s*\(\s*'DB_PASSWORD'\s*,\s*'([^']+)'\s*\)/", $cfg, $m_pass );
preg_match( "/define\s*\(\s*'DB_HOST'\s*,\s*'([^']+)'\s*\)/", $cfg, $m_host );
preg_match( "/\\\$table_prefix\s*=\s*'([^']+)'\s*;/", $cfg, $m_prefix );
$mysqli = new mysqli( $m_host[1], $m_user[1], $m_pass[1], $m_name[1] );
$prefix = $m_prefix[1];
$row = $mysqli->query( "SELECT option_id, option_value FROM {$prefix}options WHERE option_name='wp_mail_smtp' LIMIT 1" )->fetch_assoc();
$ss = @unserialize( $row['option_value'] );

$ss['mail']['mailer'] = 'smtp';
$ss['mail']['from_email'] = 'support@sunviksteels.shop';
$ss['mail']['from_name'] = 'Sunvik Steels Shop';
$ss['mail']['from_email_force'] = true;
$ss['mail']['from_name_force'] = true;
$ss['mail']['return_path'] = true;
$ss['smtp']['host'] = 'smtpout.secureserver.net';
$ss['smtp']['port'] = '465';
$ss['smtp']['encryption'] = 'ssl';
$ss['smtp']['auth'] = true;
$ss['smtp']['autotls'] = true;
if ( empty( $ss['smtp']['user'] ) ) {
	$ss['smtp']['user'] = 'support@sunviksteels.shop';
}

$serialized = serialize( $ss );
$oid = (int) $row['option_id'];
$stmt = $mysqli->prepare( "UPDATE {$prefix}options SET option_value = ? WHERE option_id = ?" );
$stmt->bind_param( 'si', $serialized, $oid );
$ok = $stmt->execute();
$report['shop_update'] = array(
	'ok' => (bool) $ok,
	'host' => $ss['smtp']['host'],
	'port' => $ss['smtp']['port'],
	'encryption' => $ss['smtp']['encryption'],
	'user' => $ss['smtp']['user'],
	'pass_set' => ! empty( $ss['smtp']['pass'] ),
	'mailer' => $ss['mail']['mailer'],
);
$stmt->close();
$mysqli->close();

// Cleanup old report files
$uploads = wp_upload_dir();
$base = trailingslashit( $uploads['basedir'] );
foreach ( array( 'sunvik-spam-fix-v1.json', 'sunvik-spam-check-v1.json' ) as $f ) {
	$p = $base . $f;
	if ( file_exists( $p ) ) {
		@unlink( $p );
	}
}
file_put_contents( $base . 'sunvik-shop-smtp-465-v1.json', wp_json_encode( $report, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES ) );
