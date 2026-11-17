/**
 * Restore shop mailer to Brevo (Sendinblue) — SMTP was hanging form submits.
 * Keep forced From = support@sunviksteels.shop.
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

$ss['mail']['mailer'] = 'sendinblue';
$ss['mail']['from_email'] = 'support@sunviksteels.shop';
$ss['mail']['from_name'] = 'Sunvik Steels Shop';
$ss['mail']['from_email_force'] = true;
$ss['mail']['from_name_force'] = true;
if ( empty( $ss['sendinblue'] ) || ! is_array( $ss['sendinblue'] ) ) {
	$ss['sendinblue'] = array();
}
$ss['sendinblue']['domain'] = 'sunviksteels.shop';

$serialized = serialize( $ss );
$oid = (int) $row['option_id'];
$stmt = $mysqli->prepare( "UPDATE {$prefix}options SET option_value = ? WHERE option_id = ?" );
$stmt->bind_param( 'si', $serialized, $oid );
$ok = $stmt->execute();
$report['restored'] = array(
	'ok' => (bool) $ok,
	'mailer' => $ss['mail']['mailer'],
	'from' => $ss['mail']['from_email'],
	'force' => $ss['mail']['from_email_force'],
	'brevo_key' => ! empty( $ss['sendinblue']['api_key'] ),
	'domain' => $ss['sendinblue']['domain'] ?? null,
);
$stmt->close();
$mysqli->close();

$uploads = wp_upload_dir();
file_put_contents( trailingslashit( $uploads['basedir'] ) . 'sunvik-shop-brevo-restore-v1.json', wp_json_encode( $report, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES ) );
