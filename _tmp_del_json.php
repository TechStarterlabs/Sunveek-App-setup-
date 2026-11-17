$uploads=wp_upload_dir();
$p=trailingslashit($uploads['basedir']).'sunvik-safe-cleanup.json';
if(file_exists($p)) @unlink($p);
