<html>
<head>
<title>Poker Hand Analytics</title>
</head>
<body>
<?php
$mysqli = new mysqli("dbase.cs.jhu.edu", "cs415_fa24_wboudy1", "QH9OaTFq8A", "cs415_fa24_wboudy1_db");
if (mysqli_connect_errno()) {
  printf("Connect failed: %s<br>", mysqli_connect_error());
  exit();
}


$mysqli->close();
?>
<br>
<a href="poker.html">Back to Home</a>
</body>
</html>