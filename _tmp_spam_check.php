$out = array( 'time' => current_time( 'mysql' ) );

$smtp = get_option( 'wp_mail_smtp' );
$out['com'] = array(
	'mailer' => $smtp['mail']['mailer'] ?? null,
	'from_email' => $smtp['mail']['from_email'] ?? null,
	'from_name' => $smtp['mail']['from_name'] ?? null,
	'from_email_force' => $smtp['mail']['from_email_force'] ?? null,
	'from_name_force' => $smtp['mail']['from_name_force'] ?? null,
	'return_path' => $smtp['mail']['return_path'] ?? null,
	'host' => $smtp['smtp']['host'] ?? null,
	'port' => $smtp['smtp']['port'] ?? null,
	'encryption' => $smtp['smtp']['encryption'] ?? null,
	'user' => $smtp['smtp']['user'] ?? null,
	'autotls' => $smtp['smtp']['autotls'] ?? null,
);

// Sample notification From on form 11835
$post = get_post( 11835 );
$data = $post ? json_decode( $post->post_content, true ) : null;
$out['com_form_from'] = array(
	'sender_address' => $data['settings']['notifications']['1']['sender_address'] ?? null,
	'sender_name' => $data['settings']['notifications']['1']['sender_name'] ?? null,
	'email_to' => $data['settings']['notifications']['1']['email'] ?? null,
);

// shop
$cfg = file_get_contents( '/home/pgf2xcsto0v0/public_html/sunviksteels.shop/wp-config.php' );
preg_match( "/define\s*\(\s*'DB_NAME'\s*,\s*'([^']+)'\s*\)/", $cfg, $m_name );
preg_match( "/define\s*\(\s*'DB_USER'\s*,\s*'([^']+)'\s*\)/", $cfg, $m_user );
preg_match( "/define\s*\(\s*'DB_PASSWORD'\s*,\s*'([^']+)'\s*\)/", $cfg, $m_pass );
preg_match( "/define\s*\(\s*'DB_HOST'\s*,\s*'([^']+)'\s*\)/", $cfg, $m_host );
preg_match( "/\\\$table_prefix\s*=\s*'([^']+)'\s*;/", $cfg, $m_prefix );
$mysqli = new mysqli( $m_host[1], $m_user[1], $m_pass[1], $m_name[1] );
$prefix = $m_prefix[1];
$row = $mysqli->query( "SELECT option_value FROM {$prefix}options WHERE option_name='wp_mail_smtp' LIMIT 1" )->fetch_assoc();
$ss = @unserialize( $row['option_value'] );
$out['shop'] = array(
	'mailer' => $ss['mail']['mailer'] ?? null,
	'from_email' => $ss['mail']['from_email'] ?? null,
	'from_name' => $ss['mail']['from_name'] ?? null,
	'from_email_force' => $ss['mail']['from_email_force'] ?? null,
	'brevo_key_set' => ! empty( $ss['sendinblue']['api_key'] ),
	'brevo_domain' => $ss['sendinblue']['domain'] ?? null,
	'smtp_host' => $ss['smtp']['host'] ?? null,
	'smtp_user' => $ss['smtp']['user'] ?? null,
);
$form = $mysqli->query( "SELECT post_content FROM {$prefix}posts WHERE ID=1866 LIMIT 1" )->fetch_assoc();
$fd = json_decode( $form['post_content'], true );
$out['shop_form_from'] = array(
	'sender_address' => $fd['settings']['notifications']['1']['sender_address'] ?? null,
	'sender_name' => $fd['settings']['notifications']['1']['sender_name'] ?? null,
	'email_to' => $fd['settings']['notifications']['1']['email'] ?? null,
);
$mysqli->close();

$uploads = wp_upload_dir();
file_put_contents( trailingslashit( $uploads['basedir'] ) . 'sunvik-spam-check-v1.json', wp_json_encode( $out, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES ) );
