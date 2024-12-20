DELIMITER //
CREATE PROCEDURE get_all_games()
BEGIN
    SELECT game_id, game_type, small_blind, big_blind 
    FROM Game 
    ORDER BY CAST(SUBSTRING(game_id, 2) AS UNSIGNED);
END //


CREATE PROCEDURE get_game_hands(IN game_id_param VARCHAR(50))
BEGIN
    SELECT h.hand_id, h.dealer_position, h.pot_size,
           GROUP_CONCAT(DISTINCT cc.card_id ORDER BY cc.street) AS community_cards
    FROM Hand h
    LEFT JOIN Community_Cards cc ON h.hand_id = cc.hand_id
    WHERE h.game_id = game_id_param
    GROUP BY h.hand_id
    ORDER BY h.hand_id;
END //


CREATE PROCEDURE get_hand_actions(IN hand_id_param VARCHAR(50))
BEGIN
    SELECT a.action_id, p.username, a.street, a.action_type, a.amount, a.action_order
    FROM Action a
    JOIN Player p ON a.player_id = p.player_id
    WHERE a.hand_id = hand_id_param
    ORDER BY a.action_order;
END //


CREATE PROCEDURE get_player_game_stats(IN game_id_param VARCHAR(50))
BEGIN
    SELECT 
        p.username,
        COUNT(DISTINCT CASE WHEN h.game_id = game_id_param THEN pih.hand_id END) as hands_played,
        SUM(CASE WHEN h.game_id = game_id_param THEN pih.amount_won ELSE 0 END) as total_profit_loss,
        SUM(CASE WHEN h.game_id = game_id_param AND a.action_type = 'bet' THEN 1 ELSE 0 END) as total_bets,
        SUM(CASE WHEN h.game_id = game_id_param AND a.action_type = 'raise' THEN 1 ELSE 0 END) as total_raises,
        SUM(CASE WHEN h.game_id = game_id_param AND a.action_type = 'fold' THEN 1 ELSE 0 END) as total_folds,
        SUM(CASE WHEN h.game_id = game_id_param AND a.action_type = 'call' THEN 1 ELSE 0 END) as total_calls,
        SUM(CASE WHEN h.game_id = game_id_param AND a.action_type = 'check' THEN 1 ELSE 0 END) as total_checks
    FROM Player p
    JOIN Played_In_Game pig ON p.player_id = pig.player_id AND pig.game_id = game_id_param
    LEFT JOIN Played_In_Hand pih ON p.player_id = pih.player_id
    LEFT JOIN Hand h ON pih.hand_id = h.hand_id
    LEFT JOIN Action a ON a.hand_id = h.hand_id AND a.player_id = p.player_id
    GROUP BY p.player_id, p.username;
END//


