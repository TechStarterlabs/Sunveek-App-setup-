
$com_config = '/home/pgf2xcsto0v0/public_html/wp-config.php';
$report = array('time' => date('c'));
if (!file_exists($com_config)) {
  $report['error'] = 'com config missing';
} else {
  $cfg = file_get_contents($com_config);
  preg_match("/define\s*\(\s*'DB_NAME'\s*,\s*'([^']+)'\s*\)/", $cfg, $m_name);
  preg_match("/define\s*\(\s*'DB_USER'\s*,\s*'([^']+)'\s*\)/", $cfg, $m_user);
  preg_match("/define\s*\(\s*'DB_PASSWORD'\s*,\s*'([^']+)'\s*\)/", $cfg, $m_pass);
  preg_match("/define\s*\(\s*'DB_HOST'\s*,\s*'([^']+)'\s*\)/", $cfg, $m_host);
  preg_match("/\$table_prefix\s*=\s*'([^']+)'\s*;/", $cfg, $m_prefix);
  $mysqli = new mysqli($m_host[1], $m_user[1], $m_pass[1], $m_name[1]);
  if ($mysqli->connect_errno) {
    $report['error'] = $mysqli->connect_error;
  } else {
    $prefix = $m_prefix[1];
    $table = $prefix . 'snippets';
    $mysqli->query("UPDATE `{$table}` SET active = 0 WHERE id = 13");
    $report['affected_13'] = $mysqli->affected_rows;
    $mysqli->query("UPDATE `{$table}` SET active = 0 WHERE name LIKE 'TEMP%'");
    $report['temps_off'] = $mysqli->affected_rows;
    $mysqli->close();
  }
}
$plugin = '/home/pgf2xcsto0v0/public_html/wp-content/plugins/code-snippets';
if (is_dir($plugin) && !is_dir($plugin . '-off')) {
  $report['rename'] = rename($plugin, $plugin . '-off');
} else {
  $report['rename'] = 'skip';
  $report['already_off'] = is_dir($plugin . '-off');
}
@file_put_contents('/home/pgf2xcsto0v0/public_html/sunviksteels.shop/wp-content/uploads/sunvik-com-fix.json', json_encode($report, JSON_PRETTY_PRINT));
