<?php
// Enable error reporting for debugging
error_reporting(E_ALL);
ini_set('display_errors', 1);

// Database connection
$mysqli = new mysqli("dbase.cs.jhu.edu", "cs415_fa24_wboudy1", "QH9OaTFq8A", "cs415_fa24_wboudy1_db");
if (mysqli_connect_errno()) {
    header('Content-Type: application/json');
    die(json_encode(["error" => "Database connection failed: " . mysqli_connect_error()]));
}

// Function to get all games
function getGames($mysqli) {
    $games = array();
    try {
        if (!$result = $mysqli->query("CALL get_all_games()")) {
            throw new Exception("Query failed: " . $mysqli->error);
        }
        
        // Fetch results
        while ($row = $result->fetch_assoc()) {
            $games[] = $row;
        }
        
        $result->close();
        
        // Clear any remaining results
        while ($mysqli->more_results()) {
            $mysqli->next_result();
        }
        
        return $games;
    } catch (Exception $e) {
        throw new Exception("Error in getGames: " . $e->getMessage());
    }
}

// Function to get game hands
function getGameHands($mysqli, $gameId) {
    $hands = array();
    try {
        $stmt = $mysqli->prepare("CALL get_game_hands(?)");
        if (!$stmt) {
            throw new Exception("Prepare failed: " . $mysqli->error);
        }
        
        $stmt->bind_param("s", $gameId);
        if (!$stmt->execute()) {
            throw new Exception("Execute failed: " . $stmt->error);
        }
        
        $result = $stmt->get_result();
        while ($row = $result->fetch_assoc()) {
            $hands[] = $row;
        }
        
        $stmt->close();
        
        // Clear any remaining results
        while ($mysqli->more_results()) {
            $mysqli->next_result();
        }
        
        return $hands;
    } catch (Exception $e) {
        throw new Exception("Error in getGameHands: " . $e->getMessage());
    }
}

// Function to get hand actions
function getHandActions($mysqli, $handId) {
    $actions = array();
    try {
        $stmt = $mysqli->prepare("CALL get_hand_actions(?)");
        if (!$stmt) {
            throw new Exception("Prepare failed: " . $mysqli->error);
        }
        
        $stmt->bind_param("s", $handId);
        if (!$stmt->execute()) {
            throw new Exception("Execute failed: " . $stmt->error);
        }
        
        $result = $stmt->get_result();
        while ($row = $result->fetch_assoc()) {
            $actions[] = $row;
        }
        
        $stmt->close();
        
        // Clear any remaining results
        while ($mysqli->more_results()) {
            $mysqli->next_result();
        }
        
        return $actions;
    } catch (Exception $e) {
        throw new Exception("Error in getHandActions: " . $e->getMessage());
    }
}

// Function to get player statistics
function getPlayerGameStats($mysqli, $gameId) {
    $stats = array();
    try {
        $stmt = $mysqli->prepare("CALL get_player_game_stats(?)");
        if (!$stmt) {
            throw new Exception("Prepare failed: " . $mysqli->error);
        }
        
        $stmt->bind_param("s", $gameId);
        if (!$stmt->execute()) {
            throw new Exception("Execute failed: " . $stmt->error);
        }
        
        $result = $stmt->get_result();
        while ($row = $result->fetch_assoc()) {
            $stats[] = $row;
        }
        
        $stmt->close();
        
        // Clear any remaining results
        while ($mysqli->more_results()) {
            $mysqli->next_result();
        }
        
        return $stats;
    } catch (Exception $e) {
        throw new Exception("Error in getPlayerGameStats: " . $e->getMessage());
    }
}

// Main request handling
header('Content-Type: application/json');

try {
    if (!isset($_GET['action'])) {
        throw new Exception("No action specified");
    }
    
    $response = null;
    
    switch ($_GET['action']) {
        case 'getGames':
            $response = getGames($mysqli);
            break;
            
        case 'getGameHands':
            if (!isset($_GET['gameId'])) {
                throw new Exception("No game ID provided");
            }
            $response = getGameHands($mysqli, $_GET['gameId']);
            break;
            
        case 'getHandActions':
            if (!isset($_GET['handId'])) {
                throw new Exception("No hand ID provided");
            }
            $response = getHandActions($mysqli, $_GET['handId']);
            break;
            
        case 'getPlayerStats':
            if (!isset($_GET['gameId'])) {
                throw new Exception("No game ID provided");
            }
            $response = getPlayerGameStats($mysqli, $_GET['gameId']);
            break;
            
        default:
            throw new Exception("Invalid action specified");
    }
    
    // Ensure we have a valid response
    if ($response === null) {
        throw new Exception("No data returned");
    }
    
    echo json_encode($response, JSON_PRETTY_PRINT);
    
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        "error" => $e->getMessage(),
        "trace" => debug_backtrace(DEBUG_BACKTRACE_IGNORE_ARGS)
    ]);
} finally {
    $mysqli->close();
}
?>