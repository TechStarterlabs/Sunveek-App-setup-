/**
 * One-shot: harden WPForms + CF7 lead emails on sunviksteels.com, send SMTP test, write report.
 * Safe to deactivate/delete after run.
 */
delete_option( 'sunvik_lead_email_setup_v1' );

$client_email = 'manjunath@sunvik.in';
$agency_email = 'ampl.seo@adworthmedia.org';
$report       = array(
	'time'          => current_time( 'mysql' ),
	'client_email'  => $client_email,
	'agency_email'  => $agency_email,
	'forms_updated' => array(),
	'cf7_updated'   => array(),
	'test_mail'     => null,
	'smtp'          => null,
	'errors'        => array(),
);

$smtp = get_option( 'wp_mail_smtp' );
if ( is_array( $smtp ) ) {
	$report['smtp'] = array(
		'mailer'     => isset( $smtp['mail']['mailer'] ) ? $smtp['mail']['mailer'] : null,
		'from_email' => isset( $smtp['mail']['from_email'] ) ? $smtp['mail']['from_email'] : null,
		'host'       => isset( $smtp['smtp']['host'] ) ? $smtp['smtp']['host'] : null,
		'port'       => isset( $smtp['smtp']['port'] ) ? $smtp['smtp']['port'] : null,
		'user'       => isset( $smtp['smtp']['user'] ) ? $smtp['smtp']['user'] : null,
		'encryption' => isset( $smtp['smtp']['encryption'] ) ? $smtp['smtp']['encryption'] : null,
		'auth'       => isset( $smtp['smtp']['auth'] ) ? $smtp['smtp']['auth'] : null,
		'pass_set'   => ! empty( $smtp['smtp']['pass'] ),
	);
}

$form_ids = array( 11835, 10265, 8468, 8431 );
foreach ( $form_ids as $fid ) {
	$post = get_post( $fid );
	if ( ! $post || $post->post_type !== 'wpforms' ) {
		$report['errors'][] = "WPForms post missing: {$fid}";
		continue;
	}

	$data = json_decode( $post->post_content, true );
	if ( ! is_array( $data ) ) {
		$report['errors'][] = "WPForms JSON decode failed: {$fid}";
		continue;
	}

	if ( ! isset( $data['settings'] ) || ! is_array( $data['settings'] ) ) {
		$data['settings'] = array();
	}

	$before = array(
		'notification_enable' => isset( $data['settings']['notification_enable'] ) ? $data['settings']['notification_enable'] : null,
		'email'               => isset( $data['settings']['notifications']['1']['email'] ) ? $data['settings']['notifications']['1']['email'] : null,
		'subject'             => isset( $data['settings']['notifications']['1']['subject'] ) ? $data['settings']['notifications']['1']['subject'] : null,
	);

	$data['settings']['notification_enable'] = '1';
	$data['settings']['ajax_submit']         = '1';

	if ( empty( $data['settings']['notifications'] ) || ! is_array( $data['settings']['notifications'] ) ) {
		$data['settings']['notifications'] = array();
	}

	// Primary client notification
	$data['settings']['notifications']['1'] = array(
		'email'          => $client_email,
		'subject'        => 'New Website Lead — {page_title}',
		'sender_name'    => 'Sunvik Steels',
		'sender_address' => 'info@sunviksteels.com',
		'replyto'        => '{field_id="2"}',
		'message'        => "A new lead was submitted on the Sunvik Steels website.\n\nPage: {page_title}\nURL: {page_url}\n\n{all_fields}",
	);

	// Secondary agency copy (tracking)
	$data['settings']['notifications']['2'] = array(
		'email'          => $agency_email,
		'subject'        => 'New Website Lead (copy) — {page_title}',
		'sender_name'    => 'Sunvik Steels',
		'sender_address' => 'info@sunviksteels.com',
		'replyto'        => '{field_id="2"}',
		'message'        => "Agency copy of website lead.\n\nPage: {page_title}\nURL: {page_url}\n\n{all_fields}",
	);

	// Keep thank-you message confirmation (do not redirect to WhatsApp)
	if ( empty( $data['settings']['confirmations']['1'] ) || ! is_array( $data['settings']['confirmations']['1'] ) ) {
		$data['settings']['confirmations'] = array(
			'1' => array(
				'type'                 => 'message',
				'message'              => '<p>Thanks for contacting us! We will be in touch with you shortly.</p>',
				'message_scroll'       => '1',
				'page'                 => '',
				'page_url_parameters' => '',
				'redirect'             => '',
			),
		);
	} else {
		$data['settings']['confirmations']['1']['type']     = 'message';
		$data['settings']['confirmations']['1']['redirect'] = '';
	}

	$new_content = wp_json_encode( $data, JSON_UNESCAPED_SLASHES );
	$updated     = wp_update_post(
		array(
			'ID'           => $fid,
			'post_content' => wp_slash( $new_content ),
		),
		true
	);

	$report['forms_updated'][] = array(
		'id'     => $fid,
		'title'  => $post->post_title,
		'before' => $before,
		'after'  => array(
			'notification_enable' => '1',
			'emails'              => array( $client_email, $agency_email ),
			'subject'             => 'New Website Lead — {page_title}',
		),
		'ok'     => ! is_wp_error( $updated ),
		'error'  => is_wp_error( $updated ) ? $updated->get_error_message() : null,
	);
}

// Align CF7 contact forms so client also receives leads
if ( class_exists( 'WPCF7_ContactForm' ) ) {
	foreach ( array( 227, 232 ) as $cf7_id ) {
		$contact = WPCF7_ContactForm::get_instance( $cf7_id );
		if ( ! $contact ) {
			$report['errors'][] = "CF7 missing: {$cf7_id}";
			continue;
		}
		$props = $contact->get_properties();
		$mail  = isset( $props['mail'] ) ? $props['mail'] : array();
		$before_to = isset( $mail['recipient'] ) ? $mail['recipient'] : '';

		$mail['active']    = true;
		$mail['recipient'] = $client_email;
		$mail['sender']    = 'Sunvik Steels <info@sunviksteels.com>';
		$mail['subject']   = 'New Contact Form Lead — [_site_title]';
		$headers           = isset( $mail['additional_headers'] ) ? (string) $mail['additional_headers'] : '';
		// Ensure Reply-To + agency Cc
		$lines = array_filter( array_map( 'trim', preg_split( '/\r\n|\r|\n/', $headers ) ) );
		$lines = array_values(
			array_filter(
				$lines,
				function ( $line ) {
					return stripos( $line, 'Cc:' ) !== 0 && stripos( $line, 'Reply-To:' ) !== 0;
				}
			)
		);
		$lines[]                   = 'Reply-To: [your-email]';
		$lines[]                   = 'Cc: ' . $agency_email;
		$mail['additional_headers'] = implode( "\n", $lines );
		$props['mail']              = $mail;
		$contact->set_properties( $props );
		$contact->save();

		$report['cf7_updated'][] = array(
			'id'        => $cf7_id,
			'title'     => $contact->title(),
			'before_to' => $before_to,
			'after_to'  => $client_email,
			'cc'        => $agency_email,
		);
	}
} else {
	$report['errors'][] = 'CF7 class not available';
}

// SMTP test email
$subject = 'Sunvik lead-email setup test — ' . current_time( 'mysql' );
$body    = "This is an automated test from sunviksteels.com after enabling form lead emails.\n\nClient recipient configured: {$client_email}\nAgency copy: {$agency_email}\n\nIf you received this, WP Mail SMTP is working.";
$headers = array( 'Content-Type: text/plain; charset=UTF-8', 'From: Sunvik Steels <info@sunviksteels.com>' );
$sent    = wp_mail( $client_email, $subject, $body, $headers );
$report['test_mail'] = array(
	'to'      => $client_email,
	'subject' => $subject,
	'sent'    => (bool) $sent,
);

$uploads = wp_upload_dir();
$path    = trailingslashit( $uploads['basedir'] ) . 'sunvik-lead-email-setup-v1.json';
file_put_contents( $path, wp_json_encode( $report, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES ) );
update_option( 'sunvik_lead_email_setup_v1', $report, false );
