$uploads=wp_upload_dir();
$p=trailingslashit($uploads['basedir']).'sunvik-leads-sep-days-v1.json';
if(file_exists($p)) @unlink($p);
