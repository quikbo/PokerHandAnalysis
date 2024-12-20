CREATE TABLE Player (
    player_id VARCHAR(12) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    country_of_birth VARCHAR(50) NOT NULL,
    city_of_birth VARCHAR(100),
    current_balance FLOAT(15,2) NOT NULL
);


CREATE TABLE Game (
    game_id VARCHAR(12) PRIMARY KEY,
    game_type VARCHAR(20) NOT NULL,
    small_blind FLOAT(15,2) NOT NULL,
    big_blind FLOAT(15,2) NOT NULL,
    min_players INT NOT NULL,
    max_players INT NOT NULL
);


CREATE TABLE Card (
    card_id VARCHAR(12) PRIMARY KEY,
    suit VARCHAR(10) NOT NULL,
    rank CHAR(1) NOT NULL
);


CREATE TABLE Hand (
    hand_id VARCHAR(12) PRIMARY KEY,
    game_id VARCHAR(12) NOT NULL,
    dealer_position INT NOT NULL,
    pot_size FLOAT(15,2) NOT NULL DEFAULT 0.00,
    FOREIGN KEY (game_id) REFERENCES Game(game_id)
);


CREATE TABLE Played_In_Game (
    player_id VARCHAR(12),
    game_id VARCHAR(12),
    buy_in_amount FLOAT(15,2) NOT NULL,
    seat_number INT NOT NULL,
    final_stack FLOAT(15,2),
    PRIMARY KEY (player_id, game_id),
    FOREIGN KEY (player_id) REFERENCES Player(player_id),
    FOREIGN KEY (game_id) REFERENCES Game(game_id)
);


CREATE TABLE Community_Cards (
    hand_id VARCHAR(12),
    card_id VARCHAR(12),
    street VARCHAR(10) NOT NULL,
    PRIMARY KEY (hand_id, card_id),
    FOREIGN KEY (hand_id) REFERENCES Hand(hand_id),
    FOREIGN KEY (card_id) REFERENCES Card(card_id)
);


CREATE TABLE Played_In_Hand (
    player_id VARCHAR(12),
    hand_id VARCHAR(12),
    card1_id VARCHAR(12),
    card2_id VARCHAR(12),
    final_result VARCHAR(15) NOT NULL,
    hand_rank VARCHAR(50),
    amount_won FLOAT(15,2),
    PRIMARY KEY (player_id, hand_id),
    FOREIGN KEY (player_id) REFERENCES Player(player_id),
    FOREIGN KEY (hand_id) REFERENCES Hand(hand_id),
    FOREIGN KEY (card1_id) REFERENCES Card(card_id),
    FOREIGN KEY (card2_id) REFERENCES Card(card_id)
);


CREATE TABLE Action (
    action_id VARCHAR(12) PRIMARY KEY,
    hand_id VARCHAR(12) NOT NULL,
    player_id VARCHAR(12) NOT NULL,
    street VARCHAR(10) NOT NULL,
    action_type VARCHAR(15) NOT NULL,
    amount FLOAT(15,2),
    action_order INT NOT NULL,
    FOREIGN KEY (hand_id) REFERENCES Hand(hand_id),
    FOREIGN KEY (player_id) REFERENCES Player(player_id)
);
