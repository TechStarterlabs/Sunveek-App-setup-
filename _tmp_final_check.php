$out = array( 'time' => current_time( 'mysql' ) );

// .com WPForms 11835
$post = get_post( 11835 );
$data = $post ? json_decode( $post->post_content, true ) : null;
$out['com_form_11835'] = array(
	'enable' => $data['settings']['notification_enable'] ?? null,
	'to1'    => $data['settings']['notifications']['1']['email'] ?? null,
	'to2'    => $data['settings']['notifications']['2']['email'] ?? null,
	'conf'   => $data['settings']['confirmations']['1']['type'] ?? null,
	'redirect' => $data['settings']['confirmations']['1']['redirect'] ?? null,
);

$smtp = get_option( 'wp_mail_smtp' );
$out['com_smtp'] = array(
	'mailer' => $smtp['mail']['mailer'] ?? null,
	'from'   => $smtp['mail']['from_email'] ?? null,
	'pass'   => ! empty( $smtp['smtp']['pass'] ),
);

// .shop via DB
$shop = '/home/pgf2xcsto0v0/public_html/sunviksteels.shop/wp-config.php';
$cfg  = file_get_contents( $shop );
preg_match( "/define\s*\(\s*'DB_NAME'\s*,\s*'([^']+)'\s*\)/", $cfg, $m_name );
preg_match( "/define\s*\(\s*'DB_USER'\s*,\s*'([^']+)'\s*\)/", $cfg, $m_user );
preg_match( "/define\s*\(\s*'DB_PASSWORD'\s*,\s*'([^']+)'\s*\)/", $cfg, $m_pass );
preg_match( "/define\s*\(\s*'DB_HOST'\s*,\s*'([^']+)'\s*\)/", $cfg, $m_host );
preg_match( "/\\\$table_prefix\s*=\s*'([^']+)'\s*;/", $cfg, $m_prefix );
$mysqli = new mysqli( $m_host[1], $m_user[1], $m_pass[1], $m_name[1] );
$prefix = $m_prefix[1];
$res = $mysqli->query( "SELECT ID, post_title, post_content FROM {$prefix}posts WHERE ID IN (1866,2276) AND post_type='wpforms'" );
$out['shop_forms'] = array();
while ( $row = $res->fetch_assoc() ) {
	$d = json_decode( $row['post_content'], true );
	$out['shop_forms'][ $row['ID'] ] = array(
		'title' => $row['post_title'],
		'enable' => $d['settings']['notification_enable'] ?? null,
		'to1' => $d['settings']['notifications']['1']['email'] ?? null,
		'to2' => $d['settings']['notifications']['2']['email'] ?? null,
		'conf' => $d['settings']['confirmations']['1']['type'] ?? null,
		'redirect' => $d['settings']['confirmations']['1']['redirect'] ?? null,
	);
}
$smtp_res = $mysqli->query( "SELECT option_value FROM {$prefix}options WHERE option_name='wp_mail_smtp' LIMIT 1" );
$smtp_row = $smtp_res->fetch_assoc();
$ss = @unserialize( $smtp_row['option_value'] );
$out['shop_smtp'] = array(
	'mailer' => $ss['mail']['mailer'] ?? null,
	'from' => $ss['mail']['from_email'] ?? null,
	'pass' => ! empty( $ss['smtp']['pass'] ) || ! empty( $ss['sendinblue']['api_key'] ),
);
$mysqli->close();

$uploads = wp_upload_dir();
file_put_contents( trailingslashit( $uploads['basedir'] ) . 'sunvik-final-check-v1.json', wp_json_encode( $out, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES ) );
