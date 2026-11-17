/**
 * Dump form leads for Sep 14, 17, 20 + confirmation/redirect history clues.
 */
$out = array( 'time' => current_time( 'mysql' ) );
global $wpdb;

$dates = array( '2026-09-14', '2026-09-17', '2026-09-20' );
$out['com_entries'] = array();

// Prefer wpforms entries table if present
$table = $wpdb->prefix . 'wpforms_entries';
$exists = $wpdb->get_var( $wpdb->prepare( 'SHOW TABLES LIKE %s', $table ) );
$out['com_entries_table'] = $exists ? $table : null;

if ( $exists ) {
	foreach ( $dates as $d ) {
		$rows = $wpdb->get_results(
			$wpdb->prepare(
				"SELECT entry_id, form_id, status, date, fields, ip_address
				 FROM {$table}
				 WHERE DATE(date) = %s
				 ORDER BY entry_id ASC",
				$d
			),
			ARRAY_A
		);
		$safe = array();
		foreach ( (array) $rows as $row ) {
			$fields = json_decode( $row['fields'], true );
			$summary = array();
			if ( is_array( $fields ) ) {
				foreach ( $fields as $f ) {
					$summary[] = array(
						'name'  => isset( $f['name'] ) ? $f['name'] : '',
						'value' => isset( $f['value'] ) ? substr( (string) $f['value'], 0, 200 ) : '',
					);
				}
			}
			$form = get_post( (int) $row['form_id'] );
			$safe[] = array(
				'entry_id' => $row['entry_id'],
				'form_id'  => $row['form_id'],
				'form'     => $form ? $form->post_title : null,
				'status'   => $row['status'],
				'date'     => $row['date'],
				'ip'       => $row['ip_address'],
				'fields'   => $summary,
			);
		}
		$out['com_entries'][ $d ] = array( 'count' => count( $safe ), 'rows' => $safe );
	}
}

// Current confirmations on main forms
foreach ( array( 11835, 8431 ) as $fid ) {
	$post = get_post( $fid );
	$data = $post ? json_decode( $post->post_content, true ) : null;
	$out['com_confirmations'][ $fid ] = array(
		'title' => $post ? $post->post_title : null,
		'confirmations' => $data['settings']['confirmations'] ?? null,
		'notifications' => array_map(
			function ( $n ) {
				return array(
					'email' => $n['email'] ?? null,
					'subject' => $n['subject'] ?? null,
				);
			},
			( $data['settings']['notifications'] ?? array() )
		),
	);
}

// Active snippets mentioning whatsapp / wpforms redirect
$snip_table = $wpdb->prefix . 'snippets';
$out['snippets_whatsapp'] = array();
if ( $wpdb->get_var( $wpdb->prepare( 'SHOW TABLES LIKE %s', $snip_table ) ) === $snip_table ) {
	$rows = $wpdb->get_results( "SELECT id, name, active, code FROM {$snip_table}", ARRAY_A );
	foreach ( (array) $rows as $r ) {
		$code = (string) $r['code'];
		if ( preg_match( '/whatsapp|wa\.me|api\.whatsapp|wpformsAjaxSubmitSuccess|confirmation.*redirect/i', $code ) ) {
			$out['snippets_whatsapp'][] = array(
				'id' => $r['id'],
				'name' => $r['name'],
				'active' => $r['active'],
				'preview' => substr( $code, 0, 500 ),
			);
		}
	}
}

// Shop entries via DB
$cfg = file_get_contents( '/home/pgf2xcsto0v0/public_html/sunviksteels.shop/wp-config.php' );
preg_match( "/define\s*\(\s*'DB_NAME'\s*,\s*'([^']+)'\s*\)/", $cfg, $m_name );
preg_match( "/define\s*\(\s*'DB_USER'\s*,\s*'([^']+)'\s*\)/", $cfg, $m_user );
preg_match( "/define\s*\(\s*'DB_PASSWORD'\s*,\s*'([^']+)'\s*\)/", $cfg, $m_pass );
preg_match( "/define\s*\(\s*'DB_HOST'\s*,\s*'([^']+)'\s*\)/", $cfg, $m_host );
preg_match( "/\\\$table_prefix\s*=\s*'([^']+)'\s*;/", $cfg, $m_prefix );
$mysqli = new mysqli( $m_host[1], $m_user[1], $m_pass[1], $m_name[1] );
$prefix = $m_prefix[1];
$out['shop_entries'] = array();
$shop_table = $prefix . 'wpforms_entries';
$chk = $mysqli->query( "SHOW TABLES LIKE '{$shop_table}'" );
if ( $chk && $chk->num_rows ) {
	foreach ( $dates as $d ) {
		$res = $mysqli->query( "SELECT entry_id, form_id, status, date, fields, ip_address FROM {$shop_table} WHERE DATE(date)='{$mysqli->real_escape_string($d)}' ORDER BY entry_id ASC" );
		$safe = array();
		while ( $row = $res->fetch_assoc() ) {
			$fields = json_decode( $row['fields'], true );
			$summary = array();
			if ( is_array( $fields ) ) {
				foreach ( $fields as $f ) {
					$summary[] = array(
						'name' => $f['name'] ?? '',
						'value' => isset( $f['value'] ) ? substr( (string) $f['value'], 0, 200 ) : '',
					);
				}
			}
			$title_res = $mysqli->query( "SELECT post_title FROM {$prefix}posts WHERE ID=" . (int) $row['form_id'] . " LIMIT 1" );
			$trow = $title_res ? $title_res->fetch_assoc() : null;
			$safe[] = array(
				'entry_id' => $row['entry_id'],
				'form_id' => $row['form_id'],
				'form' => $trow['post_title'] ?? null,
				'status' => $row['status'],
				'date' => $row['date'],
				'ip' => $row['ip_address'],
				'fields' => $summary,
			);
		}
		$out['shop_entries'][ $d ] = array( 'count' => count( $safe ), 'rows' => $safe );
	}
} else {
	$out['shop_entries_table'] = 'missing';
}

// shop confirmation for contact + gold
foreach ( array( 2276, 1866 ) as $fid ) {
	$fres = $mysqli->query( "SELECT post_title, post_content FROM {$prefix}posts WHERE ID={$fid} LIMIT 1" );
	$frow = $fres ? $fres->fetch_assoc() : null;
	$data = $frow ? json_decode( $frow['post_content'], true ) : null;
	$out['shop_confirmations'][ $fid ] = array(
		'title' => $frow['post_title'] ?? null,
		'confirmations' => $data['settings']['confirmations'] ?? null,
	);
}
$mysqli->close();

// Also list ALL com entries in September 2026 for context (counts by day)
if ( $exists ) {
	$by_day = $wpdb->get_results(
		"SELECT DATE(date) d, COUNT(*) c FROM {$table}
		 WHERE date >= '2026-09-01' AND date < '2026-10-01'
		 GROUP BY DATE(date) ORDER BY d",
		ARRAY_A
	);
	$out['com_sept_counts'] = $by_day;
}

$uploads = wp_upload_dir();
file_put_contents( trailingslashit( $uploads['basedir'] ) . 'sunvik-leads-sep-days-v1.json', wp_json_encode( $out, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES ) );
