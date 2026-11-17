/**
 * Harden mail deliverability settings for .com + .shop.
 * - Force From address alignment
 * - Switch .shop from Brevo -> GoDaddy SMTP (matches existing SPF include:secureserver.net)
 * - Send test emails
 */
$client = 'manjunath@sunvik.in';
$agency = array(
	'divya.nikam@thestarterlabs.com',
	'aaresh.kuruba@thestarterlabs.com',
	'performance@thestarterlabs.com',
);
$report = array( 'time' => current_time( 'mysql' ), 'errors' => array() );

// ---- .com WP Mail SMTP harden ----
$smtp = get_option( 'wp_mail_smtp' );
if ( ! is_array( $smtp ) ) {
	$smtp = array();
}
if ( empty( $smtp['mail'] ) || ! is_array( $smtp['mail'] ) ) {
	$smtp['mail'] = array();
}
$smtp['mail']['from_email']       = 'info@sunviksteels.com';
$smtp['mail']['from_name']        = 'Sunvik Steels';
$smtp['mail']['from_email_force'] = true;
$smtp['mail']['from_name_force']  = true;
$smtp['mail']['return_path']      = true;
$smtp['mail']['mailer']           = 'smtp';
update_option( 'wp_mail_smtp', $smtp );
$report['com_smtp_after'] = array(
	'mailer' => $smtp['mail']['mailer'],
	'from'   => $smtp['mail']['from_email'],
	'force'  => $smtp['mail']['from_email_force'],
	'return_path' => $smtp['mail']['return_path'],
	'host'   => $smtp['smtp']['host'] ?? null,
);

// ---- .shop: switch mailer to SMTP (GoDaddy) to match SPF ----
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
if ( ! is_array( $ss ) ) {
	$ss = array();
}
if ( empty( $ss['mail'] ) || ! is_array( $ss['mail'] ) ) {
	$ss['mail'] = array();
}
if ( empty( $ss['smtp'] ) || ! is_array( $ss['smtp'] ) ) {
	$ss['smtp'] = array();
}

$before_mailer = $ss['mail']['mailer'] ?? null;
$ss['mail']['mailer']           = 'smtp';
$ss['mail']['from_email']       = 'support@sunviksteels.shop';
$ss['mail']['from_name']        = 'Sunvik Steels Shop';
$ss['mail']['from_email_force'] = true;
$ss['mail']['from_name_force']  = true;
$ss['mail']['return_path']      = true;

// Prefer existing smtp credentials; ensure host matches GoDaddy outbound
if ( empty( $ss['smtp']['host'] ) ) {
	$ss['smtp']['host'] = 'smtpout.secureserver.net';
}
if ( empty( $ss['smtp']['port'] ) ) {
	$ss['smtp']['port'] = '465';
}
if ( empty( $ss['smtp']['encryption'] ) ) {
	$ss['smtp']['encryption'] = 'ssl';
}
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
$report['shop_smtp_after'] = array(
	'ok' => (bool) $ok,
	'before_mailer' => $before_mailer,
	'mailer' => $ss['mail']['mailer'],
	'from' => $ss['mail']['from_email'],
	'force' => $ss['mail']['from_email_force'],
	'host' => $ss['smtp']['host'],
	'port' => $ss['smtp']['port'],
	'user' => $ss['smtp']['user'],
	'pass_set' => ! empty( $ss['smtp']['pass'] ),
	'encryption' => $ss['smtp']['encryption'] ?? null,
);
$stmt->close();
$mysqli->close();

// ---- Test mail from .com ----
$subject = 'Sunvik inbox test (.com) — ' . current_time( 'mysql' );
$body = "Deliverability test from sunviksteels.com.\nFrom: info@sunviksteels.com via GoDaddy SMTP.\n\nPlease confirm this is in INBOX (not spam).";
$headers = array(
	'Content-Type: text/plain; charset=UTF-8',
	'From: Sunvik Steels <info@sunviksteels.com>',
	'Cc: ' . implode( ', ', $agency ),
);
$report['tests']['com'] = array(
	'to' => $client,
	'sent' => (bool) wp_mail( $client, $subject, $body, $headers ),
	'subject' => $subject,
);

$uploads = wp_upload_dir();
file_put_contents( trailingslashit( $uploads['basedir'] ) . 'sunvik-spam-fix-v1.json', wp_json_encode( $report, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES ) );
