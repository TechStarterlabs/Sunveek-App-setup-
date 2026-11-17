/**
 * Reconfigure lead emails on .com + .shop.
 * Client: manjunath@sunvik.in
 * Agency: divya.nikam / aaresh.kuruba / performance @ thestarterlabs.com
 */
$client  = 'manjunath@sunvik.in';
$agency  = array(
	'divya.nikam@thestarterlabs.com',
	'aaresh.kuruba@thestarterlabs.com',
	'performance@thestarterlabs.com',
);
$all_to  = implode( ',', array_merge( array( $client ), $agency ) );
$report  = array(
	'time'     => current_time( 'mysql' ),
	'client'   => $client,
	'agency'   => $agency,
	'all_to'   => $all_to,
	'com'      => array(),
	'shop'     => array(),
	'tests'    => array(),
	'errors'   => array(),
);

$message_tpl = "A new lead was submitted.\n\nPage: {page_title}\nURL: {page_url}\n\n{all_fields}";

// ---------- .com WPForms ----------
foreach ( array( 11835, 10265, 8468, 8431 ) as $fid ) {
	$post = get_post( $fid );
	if ( ! $post || $post->post_type !== 'wpforms' ) {
		$report['errors'][] = "com missing form {$fid}";
		continue;
	}
	$data = json_decode( $post->post_content, true );
	if ( ! is_array( $data ) ) {
		$report['errors'][] = "com decode fail {$fid}";
		continue;
	}
	if ( empty( $data['settings'] ) || ! is_array( $data['settings'] ) ) {
		$data['settings'] = array();
	}
	$data['settings']['notification_enable'] = '1';
	$data['settings']['ajax_submit']         = '1';

	$email_field = '2';
	if ( ! empty( $data['fields'] ) && is_array( $data['fields'] ) ) {
		foreach ( $data['fields'] as $fid_field => $f ) {
			if ( isset( $f['type'] ) && $f['type'] === 'email' ) {
				$email_field = (string) $fid_field;
				break;
			}
		}
	}

	$data['settings']['notifications'] = array(
		'1' => array(
			'email'          => $all_to,
			'subject'        => 'New Website Lead — {page_title}',
			'sender_name'    => 'Sunvik Steels',
			'sender_address' => 'info@sunviksteels.com',
			'replyto'        => '{field_id="' . $email_field . '"}',
			'message'        => $message_tpl,
		),
	);
	if ( empty( $data['settings']['confirmations']['1'] ) || ! is_array( $data['settings']['confirmations']['1'] ) ) {
		$data['settings']['confirmations']['1'] = array(
			'type'           => 'message',
			'message'        => '<p>Thanks for contacting us! We will be in touch with you shortly.</p>',
			'message_scroll' => '1',
			'redirect'       => '',
		);
	} else {
		$data['settings']['confirmations']['1']['type']     = 'message';
		$data['settings']['confirmations']['1']['redirect'] = '';
	}

	$updated = wp_update_post(
		array(
			'ID'           => $fid,
			'post_content' => wp_slash( wp_json_encode( $data, JSON_UNESCAPED_SLASHES ) ),
		),
		true
	);
	$report['com']['wpforms'][] = array(
		'id'    => $fid,
		'title' => $post->post_title,
		'to'    => $all_to,
		'ok'    => ! is_wp_error( $updated ),
		'error' => is_wp_error( $updated ) ? $updated->get_error_message() : null,
	);
}

// ---------- .com CF7 ----------
if ( class_exists( 'WPCF7_ContactForm' ) ) {
	foreach ( array( 227, 232 ) as $cf7_id ) {
		$contact = WPCF7_ContactForm::get_instance( $cf7_id );
		if ( ! $contact ) {
			$report['errors'][] = "com CF7 missing {$cf7_id}";
			continue;
		}
		$props = $contact->get_properties();
		$mail  = isset( $props['mail'] ) ? $props['mail'] : array();
		$mail['active']    = true;
		$mail['recipient'] = $client;
		$mail['sender']    = 'Sunvik Steels <info@sunviksteels.com>';
		$mail['subject']   = 'New Contact Form Lead — [_site_title]';
		$headers = (string) ( $mail['additional_headers'] ?? '' );
		$lines   = array_values(
			array_filter(
				array_map( 'trim', preg_split( '/\r\n|\r|\n/', $headers ) ),
				function ( $line ) {
					return $line !== '' && stripos( $line, 'Cc:' ) !== 0 && stripos( $line, 'Reply-To:' ) !== 0;
				}
			)
		);
		$lines[] = 'Reply-To: [your-email]';
		$lines[] = 'Cc: ' . implode( ', ', $agency );
		$mail['additional_headers'] = implode( "\n", $lines );
		$props['mail'] = $mail;
		$contact->set_properties( $props );
		$contact->save();
		$report['com']['cf7'][] = array(
			'id'  => $cf7_id,
			'to'  => $client,
			'cc'  => $agency,
		);
	}
}

// ---------- .com SMTP test ----------
$smtp = get_option( 'wp_mail_smtp' );
$report['com']['smtp'] = array(
	'mailer' => $smtp['mail']['mailer'] ?? null,
	'from'   => $smtp['mail']['from_email'] ?? null,
	'host'   => $smtp['smtp']['host'] ?? null,
	'port'   => $smtp['smtp']['port'] ?? null,
	'user'   => $smtp['smtp']['user'] ?? null,
	'pass'   => ! empty( $smtp['smtp']['pass'] ),
);

$subject = 'Sunvik .com lead-email test — ' . current_time( 'mysql' );
$body    = "Test from sunviksteels.com.\n\nConfigured recipients:\nClient: {$client}\nAgency: " . implode( ', ', $agency ) . "\n\nIf you got this, .com SMTP works.";
$headers = array(
	'Content-Type: text/plain; charset=UTF-8',
	'From: Sunvik Steels <info@sunviksteels.com>',
	'Cc: ' . implode( ', ', $agency ),
);
$sent = wp_mail( $client, $subject, $body, $headers );
$report['tests']['com_smtp_wp_mail'] = array( 'to' => $client, 'cc' => $agency, 'sent' => (bool) $sent, 'subject' => $subject );

// ---------- .shop via shared cPanel DB ----------
$shop_root   = '/home/pgf2xcsto0v0/public_html/sunviksteels.shop';
$config_file = $shop_root . '/wp-config.php';
if ( ! file_exists( $config_file ) ) {
	$report['errors'][] = 'shop wp-config missing';
} else {
	$cfg = file_get_contents( $config_file );
	preg_match( "/define\s*\(\s*'DB_NAME'\s*,\s*'([^']+)'\s*\)/", $cfg, $m_name );
	preg_match( "/define\s*\(\s*'DB_USER'\s*,\s*'([^']+)'\s*\)/", $cfg, $m_user );
	preg_match( "/define\s*\(\s*'DB_PASSWORD'\s*,\s*'([^']+)'\s*\)/", $cfg, $m_pass );
	preg_match( "/define\s*\(\s*'DB_HOST'\s*,\s*'([^']+)'\s*\)/", $cfg, $m_host );
	preg_match( "/\\\$table_prefix\s*=\s*'([^']+)'\s*;/", $cfg, $m_prefix );

	$mysqli = @new mysqli( $m_host[1], $m_user[1], $m_pass[1], $m_name[1] );
	if ( $mysqli->connect_errno ) {
		$report['errors'][] = 'shop DB connect failed: ' . $mysqli->connect_error;
	} else {
		$mysqli->set_charset( 'utf8mb4' );
		$prefix       = $m_prefix[1];
		$posts_table  = $prefix . 'posts';
		$options_table = $prefix . 'options';

		$res = $mysqli->query( "SELECT ID, post_title, post_content FROM `{$posts_table}` WHERE post_type='wpforms' AND post_status IN ('publish','draft')" );
		while ( $row = $res->fetch_assoc() ) {
			$fid  = (int) $row['ID'];
			$data = json_decode( $row['post_content'], true );
			if ( ! is_array( $data ) ) {
				$report['errors'][] = "shop decode fail {$fid}";
				continue;
			}
			if ( empty( $data['settings'] ) || ! is_array( $data['settings'] ) ) {
				$data['settings'] = array();
			}
			$data['settings']['notification_enable'] = '1';
			$data['settings']['ajax_submit']         = '1';

			$email_field = '2';
			if ( ! empty( $data['fields'] ) && is_array( $data['fields'] ) ) {
				foreach ( $data['fields'] as $fid_field => $f ) {
					if ( isset( $f['type'] ) && $f['type'] === 'email' ) {
						$email_field = (string) $fid_field;
						break;
					}
				}
			}

			$data['settings']['notifications'] = array(
				'1' => array(
					'email'          => $all_to,
					'subject'        => 'New Shop Lead — {page_title}',
					'sender_name'    => 'Sunvik Steels Shop',
					'sender_address' => 'support@sunviksteels.shop',
					'replyto'        => '{field_id="' . $email_field . '"}',
					'message'        => "A new lead was submitted on sunviksteels.shop.\n\nPage: {page_title}\nURL: {page_url}\n\n{all_fields}",
				),
			);
			if ( empty( $data['settings']['confirmations']['1'] ) || ! is_array( $data['settings']['confirmations']['1'] ) ) {
				$data['settings']['confirmations']['1'] = array(
					'type'           => 'message',
					'message'        => '<p>Thanks for contacting us! We will be in touch with you shortly.</p>',
					'message_scroll' => '1',
					'redirect'       => '',
				);
			} else {
				$data['settings']['confirmations']['1']['type']     = 'message';
				$data['settings']['confirmations']['1']['redirect'] = '';
			}

			$json = wp_json_encode( $data, JSON_UNESCAPED_SLASHES );
			$stmt = $mysqli->prepare( "UPDATE `{$posts_table}` SET post_content = ? WHERE ID = ?" );
			$stmt->bind_param( 'si', $json, $fid );
			$ok = $stmt->execute();
			$report['shop']['wpforms'][] = array(
				'id'    => $fid,
				'title' => $row['post_title'],
				'to'    => $all_to,
				'ok'    => (bool) $ok,
				'error' => $ok ? null : $stmt->error,
			);
			$stmt->close();
		}

		// CF7 on shop
		$cf7_res = $mysqli->query( "SELECT ID, post_title FROM `{$posts_table}` WHERE post_type='wpcf7_contact_form' AND post_status='publish'" );
		while ( $cf = $cf7_res->fetch_assoc() ) {
			$cid = (int) $cf['ID'];
			$meta_res = $mysqli->query( "SELECT meta_id, meta_value FROM `{$prefix}postmeta` WHERE post_id={$cid} AND meta_key='_mail' LIMIT 1" );
			$meta = $meta_res ? $meta_res->fetch_assoc() : null;
			if ( ! $meta ) {
				continue;
			}
			$mail = @unserialize( $meta['meta_value'] );
			if ( ! is_array( $mail ) ) {
				continue;
			}
			$mail['active']    = true;
			$mail['recipient'] = $client;
			$mail['sender']    = 'Sunvik Steels Shop <support@sunviksteels.shop>';
			$mail['subject']   = 'New Shop Contact Lead — [_site_title]';
			$headers = (string) ( $mail['additional_headers'] ?? '' );
			$lines   = array_values(
				array_filter(
					array_map( 'trim', preg_split( '/\r\n|\r|\n/', $headers ) ),
					function ( $line ) {
						return $line !== '' && stripos( $line, 'Cc:' ) !== 0 && stripos( $line, 'Reply-To:' ) !== 0;
					}
				)
			);
			$lines[] = 'Reply-To: [your-email]';
			$lines[] = 'Cc: ' . implode( ', ', $agency );
			$mail['additional_headers'] = implode( "\n", $lines );
			$serialized = serialize( $mail );
			$mid = (int) $meta['meta_id'];
			$stmt = $mysqli->prepare( "UPDATE `{$prefix}postmeta` SET meta_value = ? WHERE meta_id = ?" );
			$stmt->bind_param( 'si', $serialized, $mid );
			$ok = $stmt->execute();
			$report['shop']['cf7'][] = array( 'id' => $cid, 'title' => $cf['post_title'], 'ok' => (bool) $ok, 'to' => $client, 'cc' => $agency );
			$stmt->close();
		}

		$smtp_res = $mysqli->query( "SELECT option_value FROM `{$options_table}` WHERE option_name='wp_mail_smtp' LIMIT 1" );
		$smtp_row = $smtp_res ? $smtp_res->fetch_assoc() : null;
		if ( $smtp_row ) {
			$ss = @unserialize( $smtp_row['option_value'] );
			$report['shop']['smtp'] = array(
				'mailer' => $ss['mail']['mailer'] ?? null,
				'from'   => $ss['mail']['from_email'] ?? null,
				'host'   => $ss['smtp']['host'] ?? null,
				'brevo_key' => ! empty( $ss['sendinblue']['api_key'] ),
				'smtp_pass' => ! empty( $ss['smtp']['pass'] ),
			);
		}
		$mysqli->close();
	}
}

$uploads = wp_upload_dir();
file_put_contents(
	trailingslashit( $uploads['basedir'] ) . 'sunvik-lead-reconfig-v2.json',
	wp_json_encode( $report, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES )
);
