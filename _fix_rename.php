<?php
echo "FIXOK ";
$f = "/home/pgf2xcsto0v0/public_html/wp-content/plugins/code-snippets";
if (is_dir($f)) {
  $ok = rename($f, $f . "-off");
  echo $ok ? "RENAMED" : "RENAME_FAIL";
} else {
  echo "NOT_FOUND_OR_ALREADY_OFF";
  echo is_dir($f . "-off") ? " ALREADY_OFF" : "";
}
