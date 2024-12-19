-- Get all hands in a specific game
DELIMITER //
CREATE PROCEDURE get_game_hands(IN game_id_param VARCHAR(50))
BEGIN
    SELECT h.hand_id, h.dealer_position, h.pot_size,
           GROUP_CONCAT(DISTINCT cc.card_id ORDER BY cc.street) AS community_cards
    FROM Hand h
    LEFT JOIN Community_Cards cc ON h.hand_id = cc.hand_id
    WHERE h.game_id = game_id_param
    GROUP BY h.hand_id;
END //

-- Get player actions in a specific hand
CREATE PROCEDURE get_hand_actions(IN hand_id_param VARCHAR(50))
BEGIN
    SELECT a.action_id, p.username, a.street, a.action_type, a.amount, a.action_order
    FROM Action a
    JOIN Player p ON a.player_id = p.player_id
    WHERE a.hand_id = hand_id_param
    ORDER BY a.action_order;
END //

-- Get player statistics for a game
CREATE PROCEDURE get_player_game_stats(IN game_id_param VARCHAR(50))
BEGIN
    SELECT 
        p.username,
        COUNT(DISTINCT pih.hand_id) as hands_played,
        SUM(pih.amount_won) as total_profit_loss,
        SUM(CASE WHEN a.action_type = 'raise' THEN 1 ELSE 0 END) as total_raises,
        SUM(CASE WHEN a.action_type = 'fold' THEN 1 ELSE 0 END) as total_folds
    FROM Player p
    JOIN Played_In_Game pig ON p.player_id = pig.player_id
    JOIN Played_In_Hand pih ON p.player_id = pih.player_id
    LEFT JOIN Action a ON p.player_id = a.player_id
    WHERE pig.game_id = game_id_param
    GROUP BY p.player_id, p.username;
END //

-- Get hand history with hole cards
CREATE PROCEDURE get_detailed_hand(IN hand_id_param VARCHAR(50))
BEGIN
    SELECT 
        h.hand_id,
        h.pot_size,
        p.username,
        CONCAT(c1.rank, c1.suit, ' ', c2.rank, c2.suit) as hole_cards,
        pih.amount_won,
        pih.final_result
    FROM Hand h
    JOIN Played_In_Hand pih ON h.hand_id = pih.hand_id
    JOIN Player p ON pih.player_id = p.player_id
    JOIN Card c1 ON pih.card1_id = c1.card_id
    JOIN Card c2 ON pih.card2_id = c2.card_id
    WHERE h.hand_id = hand_id_param;
END //
