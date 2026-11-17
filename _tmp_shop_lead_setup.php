/**
 * Setup lead emails on sunviksteels.shop via same-cPanel filesystem + DB.
 * Runs from .com Code Snippets; does not bootstrap shop WP (avoids collisions).
 */
$shop_root = '/home/pgf2xcsto0v0/public_html/sunviksteels.shop';
$client    = 'manjunath@sunvik.in';
$agency    = 'ampl.seo@adworthmedia.org';
$report    = array(
	'time'      => current_time( 'mysql' ),
	'shop_root' => $shop_root,
	'exists'    => is_dir( $shop_root ),
	'errors'    => array(),
);

$config_file = $shop_root . '/wp-config.php';
if ( ! file_exists( $config_file ) ) {
	$report['errors'][] = 'shop wp-config missing';
	$uploads = wp_upload_dir();
	file_put_contents( trailingslashit( $uploads['basedir'] ) . 'sunvik-shop-lead-setup-v1.json', wp_json_encode( $report, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES ) );
	return;
}

$cfg = file_get_contents( $config_file );
preg_match( "/define\s*\(\s*'DB_NAME'\s*,\s*'([^']+)'\s*\)/", $cfg, $m_name );
preg_match( "/define\s*\(\s*'DB_USER'\s*,\s*'([^']+)'\s*\)/", $cfg, $m_user );
preg_match( "/define\s*\(\s*'DB_PASSWORD'\s*,\s*'([^']+)'\s*\)/", $cfg, $m_pass );
preg_match( "/define\s*\(\s*'DB_HOST'\s*,\s*'([^']+)'\s*\)/", $cfg, $m_host );
preg_match( "/\\\$table_prefix\s*=\s*'([^']+)'\s*;/", $cfg, $m_prefix );

$db_name = $m_name[1] ?? '';
$db_user = $m_user[1] ?? '';
$db_pass = $m_pass[1] ?? '';
$db_host = $m_host[1] ?? 'localhost';
$prefix  = $m_prefix[1] ?? 'wp_';

$report['db'] = array(
	'name'   => $db_name,
	'user'   => $db_user,
	'host'   => $db_host,
	'prefix' => $prefix,
	'pass_set' => $db_pass !== '',
);

$mysqli = @new mysqli( $db_host, $db_user, $db_pass, $db_name );
if ( $mysqli->connect_errno ) {
	$report['errors'][] = 'DB connect failed: ' . $mysqli->connect_error;
	$uploads = wp_upload_dir();
	file_put_contents( trailingslashit( $uploads['basedir'] ) . 'sunvik-shop-lead-setup-v1.json', wp_json_encode( $report, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES ) );
	return;
}
$mysqli->set_charset( 'utf8mb4' );

// List wpforms
$posts_table = $prefix . 'posts';
$options_table = $prefix . 'options';
$forms = array();
$res = $mysqli->query( "SELECT ID, post_title, post_status, post_content FROM `{$posts_table}` WHERE post_type = 'wpforms' AND post_status IN ('publish','draft') ORDER BY ID DESC" );
if ( $res ) {
	while ( $row = $res->fetch_assoc() ) {
		$forms[] = $row;
	}
}
$report['form_count'] = count( $forms );
$report['forms_before'] = array();
$report['forms_updated'] = array();

foreach ( $forms as $row ) {
	$fid  = (int) $row['ID'];
	$data = json_decode( $row['post_content'], true );
	$before_email = null;
	$before_enable = null;
	if ( is_array( $data ) && isset( $data['settings']['notifications']['1']['email'] ) ) {
		$before_email = $data['settings']['notifications']['1']['email'];
	}
	if ( is_array( $data ) && isset( $data['settings']['notification_enable'] ) ) {
		$before_enable = $data['settings']['notification_enable'];
	}
	$report['forms_before'][] = array(
		'id'    => $fid,
		'title' => $row['post_title'],
		'email' => $before_email,
		'enable'=> $before_enable,
	);

	if ( ! is_array( $data ) ) {
		$report['errors'][] = "decode fail form {$fid}";
		continue;
	}
	if ( ! isset( $data['settings'] ) || ! is_array( $data['settings'] ) ) {
		$data['settings'] = array();
	}
	$data['settings']['notification_enable'] = '1';
	$data['settings']['ajax_submit'] = '1';
	if ( empty( $data['settings']['notifications'] ) || ! is_array( $data['settings']['notifications'] ) ) {
		$data['settings']['notifications'] = array();
	}

	// Detect email field id for reply-to
	$email_field = '2';
	if ( ! empty( $data['fields'] ) && is_array( $data['fields'] ) ) {
		foreach ( $data['fields'] as $fid_field => $f ) {
			if ( isset( $f['type'] ) && $f['type'] === 'email' ) {
				$email_field = (string) $fid_field;
				break;
			}
		}
	}

	$data['settings']['notifications']['1'] = array(
		'email'          => $client,
		'subject'        => 'New Shop Lead — {page_title}',
		'sender_name'    => 'Sunvik Steels Shop',
		'sender_address' => 'info@sunviksteels.com',
		'replyto'        => '{field_id="' . $email_field . '"}',
		'message'        => "A new lead was submitted on sunviksteels.shop.\n\nPage: {page_title}\nURL: {page_url}\n\n{all_fields}",
	);
	$data['settings']['notifications']['2'] = array(
		'email'          => $agency,
		'subject'        => 'New Shop Lead (copy) — {page_title}',
		'sender_name'    => 'Sunvik Steels Shop',
		'sender_address' => 'info@sunviksteels.com',
		'replyto'        => '{field_id="' . $email_field . '"}',
		'message'        => "Agency copy of shop lead.\n\nPage: {page_title}\nURL: {page_url}\n\n{all_fields}",
	);

	if ( empty( $data['settings']['confirmations'] ) || ! is_array( $data['settings']['confirmations'] ) ) {
		$data['settings']['confirmations'] = array();
	}
	if ( empty( $data['settings']['confirmations']['1'] ) || ! is_array( $data['settings']['confirmations']['1'] ) ) {
		$data['settings']['confirmations']['1'] = array(
			'type'    => 'message',
			'message' => '<p>Thanks for contacting us! We will be in touch with you shortly.</p>',
			'message_scroll' => '1',
			'redirect' => '',
		);
	} else {
		$data['settings']['confirmations']['1']['type'] = 'message';
		$data['settings']['confirmations']['1']['redirect'] = '';
	}

	$json = wp_json_encode( $data, JSON_UNESCAPED_SLASHES );
	$stmt = $mysqli->prepare( "UPDATE `{$posts_table}` SET post_content = ? WHERE ID = ?" );
	$stmt->bind_param( 'si', $json, $fid );
	$ok = $stmt->execute();
	$report['forms_updated'][] = array(
		'id'    => $fid,
		'title' => $row['post_title'],
		'ok'    => (bool) $ok,
		'error' => $ok ? null : $stmt->error,
		'emails'=> array( $client, $agency ),
	);
	$stmt->close();
}

// CF7: update _mail postmeta for contact forms if present
$report['cf7'] = array();
$cf7_res = $mysqli->query( "SELECT ID, post_title FROM `{$posts_table}` WHERE post_type = 'wpcf7_contact_form' AND post_status = 'publish'" );
if ( $cf7_res ) {
	while ( $cf = $cf7_res->fetch_assoc() ) {
		$cid = (int) $cf['ID'];
		$meta_res = $mysqli->query( "SELECT meta_id, meta_value FROM `{$prefix}postmeta` WHERE post_id = {$cid} AND meta_key = '_mail' LIMIT 1" );
		$meta = $meta_res ? $meta_res->fetch_assoc() : null;
		if ( ! $meta ) {
			$report['cf7'][] = array( 'id' => $cid, 'title' => $cf['post_title'], 'skipped' => 'no _mail' );
			continue;
		}
		$mail = @unserialize( $meta['meta_value'] );
		if ( ! is_array( $mail ) ) {
			$report['cf7'][] = array( 'id' => $cid, 'title' => $cf['post_title'], 'skipped' => 'unserialize fail' );
			continue;
		}
		$before = $mail['recipient'] ?? '';
		$mail['active'] = true;
		$mail['recipient'] = $client;
		$mail['sender'] = 'Sunvik Steels Shop <info@sunviksteels.com>';
		$mail['subject'] = 'New Shop Contact Lead — [_site_title]';
		$headers = (string) ( $mail['additional_headers'] ?? '' );
		$lines = array_values( array_filter( array_map( 'trim', preg_split( '/\r\n|\r|\n/', $headers ) ), function ( $line ) {
			return $line !== '' && stripos( $line, 'Cc:' ) !== 0 && stripos( $line, 'Reply-To:' ) !== 0;
		} ) );
		$lines[] = 'Reply-To: [your-email]';
		$lines[] = 'Cc: ' . $agency;
		$mail['additional_headers'] = implode( "\n", $lines );
		$serialized = serialize( $mail );
		$mid = (int) $meta['meta_id'];
		$stmt = $mysqli->prepare( "UPDATE `{$prefix}postmeta` SET meta_value = ? WHERE meta_id = ?" );
		$stmt->bind_param( 'si', $serialized, $mid );
		$ok = $stmt->execute();
		$report['cf7'][] = array(
			'id' => $cid,
			'title' => $cf['post_title'],
			'before' => $before,
			'after' => $client,
			'ok' => (bool) $ok,
		);
		$stmt->close();
	}
}

// Read shop SMTP option if present
$smtp_res = $mysqli->query( "SELECT option_value FROM `{$options_table}` WHERE option_name = 'wp_mail_smtp' LIMIT 1" );
$smtp_row = $smtp_res ? $smtp_res->fetch_assoc() : null;
if ( $smtp_row ) {
	$smtp = @unserialize( $smtp_row['option_value'] );
	if ( is_array( $smtp ) ) {
		$report['smtp'] = array(
			'mailer' => $smtp['mail']['mailer'] ?? null,
			'from_email' => $smtp['mail']['from_email'] ?? null,
			'host' => $smtp['smtp']['host'] ?? null,
			'port' => $smtp['smtp']['port'] ?? null,
			'user' => $smtp['smtp']['user'] ?? null,
			'pass_set' => ! empty( $smtp['smtp']['pass'] ),
		);
	}
} else {
	$report['smtp'] = null;
}

// Active plugins hint
$plug_res = $mysqli->query( "SELECT option_value FROM `{$options_table}` WHERE option_name = 'active_plugins' LIMIT 1" );
$plug_row = $plug_res ? $plug_res->fetch_assoc() : null;
if ( $plug_row ) {
	$plugins = @unserialize( $plug_row['option_value'] );
	$report['active_plugins_relevant'] = array_values( array_filter( (array) $plugins, function ( $p ) {
		$p = strtolower( (string) $p );
		return strpos( $p, 'wpforms' ) !== false || strpos( $p, 'mail' ) !== false || strpos( $p, 'smtp' ) !== false || strpos( $p, 'contact-form' ) !== false || strpos( $p, 'whatsapp' ) !== false;
	} ) );
}

$admin_res = $mysqli->query( "SELECT option_value FROM `{$options_table}` WHERE option_name = 'admin_email' LIMIT 1" );
$admin_row = $admin_res ? $admin_res->fetch_assoc() : null;
$report['admin_email'] = $admin_row['option_value'] ?? null;
$report['client_email'] = $client;
$report['agency_email'] = $agency;

$mysqli->close();

$uploads = wp_upload_dir();
$path = trailingslashit( $uploads['basedir'] ) . 'sunvik-shop-lead-setup-v1.json';
file_put_contents( $path, wp_json_encode( $report, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES ) );
