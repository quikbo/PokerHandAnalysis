<html>
<head>
    <title>Poker Hand Analytics</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .container { margin-top: 20px; }
        .hand-details { margin-top: 15px; }
    </style>
</head>
<body>
<?php
$mysqli = new mysqli("dbase.cs.jhu.edu", "cs415_fa24_wboudy1", "QH9OaTFq8A", "cs415_fa24_wboudy1_db");
if (mysqli_connect_errno()) {
    printf("Connect failed: %s<br>", mysqli_connect_error());
    exit();
}

// Function to get all games
function getGames($mysqli) {
  $games = array();
  $query = "CALL get_all_games()";  // Stored procedure
  if ($result = $mysqli->query($query)) {
      while ($row = $result->fetch_assoc()) {
          $games[] = $row;
      }
      $result->free();
  }
  return $games;
}

// Function to get hands in a game
function getGameHands($mysqli, $gameId) {
  $hands = array();
  $query = "CALL get_game_hands(?)";  // Stored procedure
  if ($stmt = $mysqli->prepare($query)) {
      $stmt->bind_param("s", $gameId);
      $stmt->execute();
      $result = $stmt->get_result();
      while ($row = $result->fetch_assoc()) {
          $hands[] = $row;
      }
      $stmt->close();
  }
  return $hands;
}

// Function to get hand actions
function getHandActions($mysqli, $handId) {
  $actions = array();
  $query = "CALL get_hand_actions(?)";  // Stored procedure
  if ($stmt = $mysqli->prepare($query)) {
      $stmt->bind_param("s", $handId);
      $stmt->execute();
      $result = $stmt->get_result();
      while ($row = $result->fetch_assoc()) {
          $actions[] = $row;
      }
      $stmt->close();
  }
  return $actions;
}

// Function to get player statistics
function getPlayerGameStats($mysqli, $gameId) {
  $stats = array();
  $query = "CALL get_player_game_stats(?)";  // Stored procedure
  if ($stmt = $mysqli->prepare($query)) {
      $stmt->bind_param("s", $gameId);
      $stmt->execute();
      $result = $stmt->get_result();
      while ($row = $result->fetch_assoc()) {
          $stats[] = $row;
      }
      $stmt->close();
  }
  return $stats;
}

// Handle AJAX requests
if (isset($_GET['action'])) {
    header('Content-Type: application/json');
    
    switch ($_GET['action']) {
        case 'getGames':
            echo json_encode(getGames($mysqli));
            break;
        case 'getGameHands':
            if (isset($_GET['gameId'])) {
                echo json_encode(getGameHands($mysqli, $_GET['gameId']));
            }
            break;
        case 'getHandActions':
            if (isset($_GET['handId'])) {
                echo json_encode(getHandActions($mysqli, $_GET['handId']));
            }
            break;
        case 'getPlayerStats':
            if (isset($_GET['gameId'])) {
                echo json_encode(getPlayerGameStats($mysqli, $_GET['gameId']));
            }
            break;
    }
    $mysqli->close();
    exit;
}
?>

<div class="container">
    <h1>Poker Game Analysis</h1>
    
    <div class="row">
        <div class="col-md-4">
            <h3>Select Game</h3>
            <select id="gameSelect" class="form-select">
                <option value="">Select a game...</option>
                <?php
                $games = getGames($mysqli);
                foreach ($games as $game) {
                    echo "<option value='{$game['game_id']}'>{$game['game_id']} - SB: {$game['small_blind']}, BB: {$game['big_blind']}</option>";
                }
                ?>
            </select>
        </div>
        
        <div class="col-md-8">
            <h3>Player Statistics</h3>
            <div id="playerStats"></div>
        </div>
    </div>
    
    <div class="row mt-4">
        <div class="col-md-12">
            <h3>Hand History</h3>
            <div id="handHistory"></div>
        </div>
    </div>
</div>

<br>
<a href="poker.html" class="btn btn-primary">Back to Home</a>

<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script>
    $(document).ready(function() {
        $('#gameSelect').change(function() {
            const gameId = $(this).val();
            if (!gameId) return;

            // Load player statistics
            $.get(window.location.href, {
                action: 'getPlayerStats',
                gameId: gameId
            }, function(data) {
                let html = '<table class="table"><thead><tr><th>Player</th><th>Hands</th><th>Profit/Loss</th><th>Raises</th><th>Folds</th></tr></thead><tbody>';
                data.forEach(player => {
                    html += `<tr>
                        <td>${player.username}</td>
                        <td>${player.hands_played}</td>
                        <td>${player.total_profit_loss}</td>
                        <td>${player.total_raises}</td>
                        <td>${player.total_folds}</td>
                    </tr>`;
                });
                html += '</tbody></table>';
                $('#playerStats').html(html);
            });

            // Load hands
            $.get(window.location.href, {
                action: 'getGameHands',
                gameId: gameId
            }, function(data) {
                let html = '<div class="accordion" id="handsAccordion">';
                data.forEach((hand, index) => {
                    html += `
                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#hand${index}">
                                    Hand ${hand.hand_id} - Pot: $${hand.pot_size}
                                </button>
                            </h2>
                            <div id="hand${index}" class="accordion-collapse collapse" data-hand-id="${hand.hand_id}">
                                <div class="accordion-body">
                                    <p>Community Cards: ${hand.community_cards || 'None'}</p>
                                    <div class="actions-${hand.hand_id}"></div>
                                </div>
                            </div>
                        </div>`;
                });
                html += '</div>';
                $('#handHistory').html(html);
            });
        });

        // Load hand actions when expanding accordion
        $(document).on('show.bs.collapse', '.accordion-collapse', function() {
            const handId = $(this).data('hand-id');
            const actionsDiv = $(`.actions-${handId}`);
            
            $.get(window.location.href, {
                action: 'getHandActions',
                handId: handId
            }, function(data) {
                let html = '<table class="table"><thead><tr><th>Player</th><th>Street</th><th>Action</th><th>Amount</th></tr></thead><tbody>';
                data.forEach(action => {
                    html += `<tr>
                        <td>${action.username}</td>
                        <td>${action.street}</td>
                        <td>${action.action_type}</td>
                        <td>${action.amount || '-'}</td>
                    </tr>`;
                });
                html += '</tbody></table>';
                actionsDiv.html(html);
            });
        });
    });
</script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>

<?php
$mysqli->close();
?>
</body>
</html>