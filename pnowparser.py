import csv

PLAYER_MAP = {
    'bFVCtPV6Yr': 'bing',
    '1y_5Rmubr_': 'bo'
}

PLAYER_ID_MAP = {
    'bing': 'Player7',
    'bo': 'Player8'
}

def convert_suit(card):
    if not card:
        return None
    if isinstance(card, str):
        card = card.strip()
        if card.startswith('10'):
            rank = 'T'  #convert 10 to T
            suit = card[2]  
        else:
            rank = card[0]
            suit = card[1]
        suit_map = {
            '♠': 's',
            '♥': 'h',
            '♦': 'd',
            '♣': 'c'
        }
        return f"{rank}{suit_map.get(suit, suit.lower())}"
    return None

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

def format_value(v):
    if v is None:
        return 'null'
    elif isinstance(v, (int, float)):
        return str(v)
    else:
        return f"'{str(v)}'"

def get_player_id(player_name):
    try:
        unique_code = player_name.split(' @ ')[1].split('"')[0] if ' @ ' in player_name else player_name
        username = PLAYER_MAP.get(unique_code, player_name)
        return PLAYER_ID_MAP.get(username, 'Player7')
    except Exception:
        print(f"Error processing player name: {player_name}")
        return 'Player7'

def parse_cards(card_text):
    if not card_text:
        return None, None
    cards = [c.strip() for c in card_text.split(',')]
    if len(cards) != 2:
        return None, None
    return convert_suit(cards[0]), convert_suit(cards[1])

def write_sql_insert(f, table, columns, values):
    if len(columns) != len(values):
        raise ValueError("Number of columns must match number of values")
    formatted_values = [format_value(v) for v in values]
    sql_insert = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(formatted_values)});\n"
    f.write(sql_insert)

def parse_poker_now_log(csv_file, output_file):
    with open(output_file, 'w') as f:
        write_sql_insert(f, 'Player', 
            ['player_id', 'username', 'email', 'password', 'country_of_birth', 'current_balance'],
            ['Player7', 'bing', 'bing@example.com', 'hashed_password', 'USA', 10000])
        write_sql_insert(f, 'Player',
            ['player_id', 'username', 'email', 'password', 'country_of_birth', 'current_balance'],
            ['Player8', 'bo', 'bo@example.com', 'hashed_password', 'USA', 10000])
        write_sql_insert(f, 'Game',
            ['game_id', 'game_type', 'small_blind', 'big_blind', 'min_players', 'max_players'],
            ['G200', 'NT', 0.10, 0.20, 2, 2])
        write_sql_insert(f, 'Played_In_Game',
            ['player_id', 'game_id', 'buy_in_amount', 'seat_number', 'final_stack'],
            ['Player7', 'G200', 10000, 1, 10000])
        write_sql_insert(f, 'Played_In_Game',
            ['player_id', 'game_id', 'buy_in_amount', 'seat_number', 'final_stack'],
            ['Player8', 'G200', 10000, 2, 10000])
        f.write('\n')

        current_hand = None
        hand_num = 1
        action_num = 1
        hand_players = set()
        shown_hands = {}
        pot_size = 0
        player_investments = {}
        hand_statements = []
        other_statements = []

        def write_buffered_statement(table, columns, values, is_hand=False):
            formatted_values = [format_value(v) for v in values]
            sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(formatted_values)});\n"
            if is_hand:
                hand_statements.append(sql)
            else:
                other_statements.append(sql)

        with open(csv_file, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            entries = list(reader)
            entries.reverse()
            for entry in entries:
                text = entry['entry']
                if '-- starting hand' in text:
                    if current_hand:
                        write_buffered_statement('Hand',
                            ['hand_id', 'game_id', 'dealer_position', 'pot_size'],
                            [current_hand['id'], 'G200', 1, pot_size],
                            is_hand=True)
                        f.write(''.join(hand_statements))
                        f.write(''.join(other_statements))
                        f.write('\n')
                        hand_statements = []
                        other_statements = []
                        hand_num += 1
                    current_hand = {
                        'id': f'H200_{hand_num}',
                        'current_street': 'preflop'
                    }
                    hand_players = set()
                    shown_hands = {}
                    pot_size = 0
                    player_investments = {}
                #process players
                if 'shows' in text or 'posts' in text.lower():
                    player = text.split(' @ ')[1].split('"')[0]
                    hand_players.add(player)
                #process hole cards
                if 'shows a' in text:
                    player = text.split(' @ ')[1].split('"')[0]
                    cards_text = text.split('shows a ')[1].strip('.')
                    card1, card2 = parse_cards(cards_text)
                    shown_hands[player] = (card1, card2)
                elif 'Your hand is' in text:
                    cards_text = text.split('Your hand is ')[1]
                    card1, card2 = parse_cards(cards_text)
                    shown_hands['bFVCtPV6Yr'] = (card1, card2)
                #community cards
                elif any(s in text for s in ['Flop:', 'Turn:', 'River:']):
                    if 'Flop:' in text:
                        current_hand['current_street'] = 'flop'
                        cards = text.split('[')[1].split(']')[0].split(',')
                        for card in cards:
                            write_buffered_statement('Community_Cards',
                                ['hand_id', 'card_id', 'street'],
                                [current_hand['id'], convert_suit(card.strip()), 'flop'])
                    elif 'Turn:' in text:
                        current_hand['current_street'] = 'turn'
                        card = text.split('[')[1].split(']')[0]
                        write_buffered_statement('Community_Cards',
                            ['hand_id', 'card_id', 'street'],
                            [current_hand['id'], convert_suit(card.strip()), 'turn'])
                    elif 'River:' in text:
                        current_hand['current_street'] = 'river'
                        card = text.split('[')[1].split(']')[0]
                        write_buffered_statement('Community_Cards',
                            ['hand_id', 'card_id', 'street'],
                            [current_hand['id'], convert_suit(card.strip()), 'river'])
                #actions & pot size calcs
                elif any(action in text.lower() for action in ['posts', 'raises', 'calls', 'folds', 'checks']):
                    if current_hand:
                        player = get_player_id(text.split(' @ ')[1].split('"')[0])
                        action_type = get_action_type(text)
                        amount = None
                        if 'raises to' in text:
                            new_amount = float(text.split('raises to ')[1].split()[0])
                            amount = new_amount - player_investments.get(player, 0)
                            player_investments[player] = new_amount
                            pot_size += amount
                        elif 'calls' in text:
                            amount = float(text.split('calls ')[1].split()[0])
                            player_investments[player] = player_investments.get(player, 0) + amount
                            pot_size += amount
                        elif 'posts' in text:
                            amount = float(text.split('of ')[1])
                            player_investments[player] = player_investments.get(player, 0) + amount
                            pot_size += amount
                        write_buffered_statement('Action',
                            ['action_id', 'hand_id', 'player_id', 'street', 'action_type', 'amount', 'action_order'],
                            [f'A{hand_num}_{action_num}', current_hand['id'], 
                             player, current_hand['current_street'],
                             action_type, amount, action_num])
                        action_num += 1
                #final results
                elif 'collected' in text:
                    player = get_player_id(text.split(' @ ')[1].split('"')[0])
                    amount_won = float(text.split('collected ')[1].split(' from')[0])
        
                    for p_id, invested in player_investments.items():
                        player_code = [k for k, v in PLAYER_MAP.items() if PLAYER_ID_MAP[v] == p_id][0]
                        cards = shown_hands.get(player_code, (None, None))
                        final_result = round(amount_won - invested if p_id == player else -invested, 2)
                        write_buffered_statement('Played_In_Hand',
                            ['player_id', 'hand_id', 'card1_id', 'card2_id', 'final_result', 'hand_rank', 'amount_won'],
                            [p_id, current_hand['id'], cards[0], cards[1], final_result, None, final_result])

                if '-- ending hand' in text:
                    for player in hand_players - set(shown_hands.keys()):
                        if player not in player_investments:
                            continue
                        invested = player_investments[player]
                        final_result = round(-invested, 2)
                        write_buffered_statement('Played_In_Hand',
                            ['player_id', 'hand_id', 'card1_id', 'card2_id', 'final_result', 'hand_rank', 'amount_won'],
                            [get_player_id(player), current_hand['id'], None, None, final_result, None, final_result])
                    action_num = 1
        if current_hand:
            write_buffered_statement('Hand',
                ['hand_id', 'game_id', 'dealer_position', 'pot_size'],
                [current_hand['id'], 'G200', 1, pot_size],
                is_hand=True)
            f.write(''.join(hand_statements))
            f.write(''.join(other_statements))

if __name__ == "__main__":
    parse_poker_now_log('../pokernowlog.csv', '../pnow_hands.sql')