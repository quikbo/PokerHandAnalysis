import csv

def convert_suit(card):
    if card.startswith('10'):
        rank = 'T'
        suit = card[2]
    else:
        rank, suit = card[0], card[1]
    
    suit_map = {
        '♠': 's',
        '♥': 'h',
        '♦': 'd',
        '♣': 'c'
    }
    return f"C{rank}{suit_map.get(suit, suit.lower())}"

def get_action_type(text):
    if 'raises' in text:
        return 'raise'
    elif 'calls' in text:
        return 'call'
    elif 'folds' in text:
        return 'fold'
    elif 'posts a small blind' in text:
        return 'sb'
    elif 'posts a big blind' in text:
        return 'bb'
    elif 'checks' in text:
        return 'check'
    return 'bet'

def write_sql_insert(f, table, columns, values):
    # Ensure columns and values have the same length
    if len(columns) != len(values):
        raise ValueError("Number of columns must match number of values")
    
    # Format each value appropriately for SQL
    def format_value(v):
        if v is None:
            return 'null'
        elif isinstance(v, (int, float)):
            return str(v)
        else:
            return f"'{str(v)}'"
    
    # Create the formatted SQL insert statement
    formatted_values = [format_value(v) for v in values]
    sql_insert = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(formatted_values)});\n"
    
    # Write the statement to the file
    f.write(sql_insert)

def get_player_id(player_name):
    player_map = {
        'bFVCtPV6Yr': 'bing',
        '1y_5Rmubr_': 'bo'
    }
    
    try:
        # Try to extract the unique code from the player name
        unique_code = player_name.split(' @ ')[1].split('"')[0] if ' @ ' in player_name else player_name
        
        # Map the unique code to the player name
        username = player_map.get(unique_code, player_name)
        
        # Map username to player ID
        player_id_map = {
            'bing': 'Player1',
            'bo': 'Player2'
        }
        
        return player_id_map.get(username, 'Player1')
    except Exception:
        # Fallback to a default if parsing fails
        print(player_name)
        return 'Player1'

def parse_poker_now_log(csv_file, output_file):
    with open(output_file, 'w') as f:
        # Write initial player and game data
        write_sql_insert(f, 'Player', 
            ['player_id', 'username', 'email', 'password', 'country_of_birth', 'current_balance'],
            ['Player1', 'bing', 'bing@example.com', 'hashed_password', 'USA', 10000])
        write_sql_insert(f, 'Player',
            ['player_id', 'username', 'email', 'password', 'country_of_birth', 'current_balance'],
            ['Player2', 'bo', 'bo@example.com', 'hashed_password', 'USA', 10000])
        write_sql_insert(f, 'Game',
            ['game_id', 'game_type', 'small_blind', 'big_blind', 'min_players', 'max_players'],
            ['G100', 'NT', 0.10, 0.20, 2, 2])
        write_sql_insert(f, 'Played_In_Game',
            ['player_id', 'game_id', 'buy_in_amount', 'seat_number', 'final_stack'],
            ['Player1', 'G100', 10000, 1, 10000])
        write_sql_insert(f, 'Played_In_Game',
            ['player_id', 'game_id', 'buy_in_amount', 'seat_number', 'final_stack'],
            ['Player2', 'G100', 10000, 2, 10000])
        f.write('\n')

        current_hand = None
        hand_num = 1
        action_num = 1
        hand_players = set()
        shown_hands = {}

        with open(csv_file, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            entries = list(reader)
            entries.reverse()
            
            for entry in entries:
                text = entry['entry']
                
                if '-- starting hand' in text:
                    if current_hand:
                        # Process any unshown hands from previous hand
                        for player in hand_players - set(shown_hands.keys()):
                            write_sql_insert(f, 'Played_In_Hand',
                                ['player_id', 'hand_id', 'card1_id', 'card2_id', 'final_result', 'hand_rank', 'amount_won'],
                                [get_player_id(player), current_hand['id'], None, None, 'not_shown', None, 0])
                        
                        hand_num += 1
                    
                    # Reset tracking for new hand
                    current_hand = {
                        'id': f'H100_{hand_num}',
                        'community_cards': [],
                        'actions': [],
                        'current_street': 'preflop'
                    }
                    hand_players = set()
                    shown_hands = {}
                    
                    write_sql_insert(f, 'Hand',
                        ['hand_id', 'game_id', 'dealer_position', 'pot_size'],
                        [current_hand['id'], 'G100', 1, 0.0])

                # Track players in the hand
                if 'shows a' in text or 'posts' in text.lower():
                    player = text.split(' @ ')[1].split('"')[0]
                    hand_players.add(player)

                # Process hand showdowns
                if 'shows a' in text:
                    player = text.split(' @ ')[1].split('"')[0]
                    cards = text.split('shows a ')[1].strip('.')
                    card1, card2 = map(convert_suit, cards.split(', '))
                    
                    write_sql_insert(f, 'Played_In_Hand',
                        ['player_id', 'hand_id', 'card1_id', 'card2_id', 'final_result', 'hand_rank', 'amount_won'],
                        [get_player_id(player), current_hand['id'], card1, card2, 'shown', None, 0])
                    
                    shown_hands[player] = (card1, card2)

                elif any(s in text for s in ['Flop:', 'Turn:', 'River:']):
                    if 'Flop:' in text:
                        current_hand['current_street'] = 'flop'
                        cards = text.split('Flop:')[1].strip('[] \n').split(', ')
                        for card in cards:
                            write_sql_insert(f, 'Community_Cards',
                                ['hand_id', 'card_id', 'street'],
                                [current_hand['id'], convert_suit(card), 'flop'])
                    elif 'Turn:' in text:
                        current_hand['current_street'] = 'turn'
                        card = text.split('[')[1].strip('[] \n')
                        write_sql_insert(f, 'Community_Cards',
                            ['hand_id', 'card_id', 'street'],
                            [current_hand['id'], convert_suit(card), 'turn'])
                    elif 'River:' in text:
                        current_hand['current_street'] = 'river'
                        card = text.split('[')[1].strip('[] \n')
                        write_sql_insert(f, 'Community_Cards',
                            ['hand_id', 'card_id', 'street'],
                            [current_hand['id'], convert_suit(card), 'river'])

                elif any(action in text.lower() for action in ['posts', 'raises', 'calls', 'folds', 'checks']):
                    if current_hand:
                        player = text.split(' @ ')[1].split('"')[0]
                        action_type = get_action_type(text)
                        amount = None
                        if 'raises to' in text:
                            amount = float(text.split('raises to ')[1].split(' ')[0])
                        elif 'posts a' in text:
                            amount = float(text.split('of ')[1])
                        
                        write_sql_insert(f, 'Action',
                            ['action_id', 'hand_id', 'player_id', 'street', 'action_type', 'amount', 'action_order'],
                            [f'A{hand_num}_{action_num}', current_hand['id'], 
                             get_player_id(player), current_hand['current_street'],
                             action_type, amount, action_num])
                        action_num += 1

                if '-- ending hand' in text:
                    # Process any unshown hands
                    for player in hand_players - set(shown_hands.keys()):
                        write_sql_insert(f, 'Played_In_Hand',
                            ['player_id', 'hand_id', 'card1_id', 'card2_id', 'final_result', 'hand_rank', 'amount_won'],
                            [get_player_id(player), current_hand['id'], None, None, 'not_shown', None, 0])
                    
                    f.write('\n')
                    action_num = 1

if __name__ == "__main__":
    parse_poker_now_log('pokernowlog.csv', 'pnow_hands.sql')