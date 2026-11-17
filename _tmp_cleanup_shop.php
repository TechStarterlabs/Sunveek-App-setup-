 = wp_upload_dir();
 = trailingslashit( \['basedir'] );
foreach ( array('sunvik-shop-lead-setup-v1.json','sunvik-cpanel-scan-v1.json','sunvik-lead-email-verify-v1.json','sunvik-lead-email-setup-v1.json') as \ ) {
  \ = \ . \; if (file_exists(\)) @unlink(\);
}
