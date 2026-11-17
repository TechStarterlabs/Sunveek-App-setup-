$uploads = wp_upload_dir();
$p = trailingslashit($uploads['basedir']).'sunvik-shop-smtp-465-v1.json';
if (file_exists($p)) @unlink($p);
