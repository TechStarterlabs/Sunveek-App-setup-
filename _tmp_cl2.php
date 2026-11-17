$uploads = wp_upload_dir();
foreach (array('sunvik-shop-brevo-restore-v1.json','sunvik-shop-smtp-465-v1.json','sunvik-spam-fix-v1.json','sunvik-spam-check-v1.json') as $f) {
  $p = trailingslashit($uploads['basedir']).$f; if (file_exists($p)) @unlink($p);
}
