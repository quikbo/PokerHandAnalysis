import os
from typing import List, Dict
import ast


def parse_text_file(filename: str) -> Dict:
    'open and parse text file into dict'
    data = {}
    with open(filename, 'r') as file:
        for line in file:
            if not line.strip():
                continue
                
            parts = line.strip().split(' = ')
            if len(parts) != 2:
                continue
                
            key, value = parts
            
            if key == 'actions':
                try:
                    value = ast.literal_eval(value)
                except:
                    print(f"Error parsing actions line: {value}")
                    continue
            elif value.startswith('[') and value.endswith(']'):
                try:
                    value = ast.literal_eval(value)
                except:
                    value = value[1:-1]
                    if value:
                        if ',' in value:
                            value = [x.strip() for x in value.split(',')]
                            value = [float(x) if '.' in x else int(x) if x.strip().isdigit() else x for x in value]
                        else:
                            value = [x.strip("'") for x in value.split()]
            elif value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            elif value.isdigit():
                value = int(value)
            elif value.replace('.', '').isdigit():
                value = float(value)
                
            data[key] = value
    
    return data


def calculate_pot_size(actions: List[str], blinds: List[float]) -> float:
    """Calculate total pot size by tracking all bets and raises through the hand."""
    pot_size = sum(blinds)  # Start with blinds
    for action in actions:
        parts = action.split()
        if parts[0] == 'd':  # dealer action
            continue
        if parts[1] in ['cbr', 'cc']:  # bet/raise or call
            if len(parts) > 2:  # has amount
                try:
                    pot_size += float(parts[2])
                except ValueError:
                    continue
    return pot_size


class SQLGenerator:
    def __init__(self, game_folder: str):
        self.game_folder = game_folder
        self.player_ids = {}
        self.card_ids = {}
        self.hand_counter = 0
        self.action_counter = 0
        self.player_counter = 0
        self.dealer_position = 6

    def get_and_rotate_dealer(self) -> int:
        current_dealer = self.dealer_position
        self.dealer_position = self.dealer_position - 1 if self.dealer_position > 1 else 6
        return current_dealer
        
    def get_player_id(self, username: str) -> str:
        if username not in self.player_ids:
            self.player_counter += 1
            self.player_ids[username] = f"Player{self.player_counter}"
        return self.player_ids[username]
        
    def get_card_id(self, rank: str, suit: str) -> str:
        key = f"{rank}{suit}"
        if key not in self.card_ids:
            self.card_ids[key] = f"{rank}{suit}"
        return self.card_ids[key]

    def determine_street(self, actions: List[str], current_action_index: int) -> str:
        board_cards_seen = 0
        for i in range(current_action_index):
            parts = actions[i].split()
            if parts[0] == 'd' and parts[1] == 'db':
                board_cards_seen += len(parts[2]) // 2

        if board_cards_seen == 0:
            return 'preflop'
        elif board_cards_seen == 3:
            return 'flop'
        elif board_cards_seen == 4:
            return 'turn'
        elif board_cards_seen == 5:
            return 'river'
        return 'preflop'

    def determine_action_type(self, action: str, street: str, previous_actions: List[str]) -> str:
        parts = action.split()
        action_code = parts[1]
        
        if action_code == 'f':
            return 'fold'
        elif action_code == 'cc':
            # check or call by looking at prev actions in same street
            is_check = True
            current_street_actions = []
            for prev_action in previous_actions:
                prev_parts = prev_action.split()
                if prev_parts[0] == 'd' and prev_parts[1] == 'db':  # new street
                    current_street_actions = []
                elif prev_parts[0] != 'd':
                    current_street_actions.append(prev_action)
                    
            for prev_action in current_street_actions:
                prev_parts = prev_action.split()
                if prev_parts[1] == 'cbr':  # If there was a bet/raise before
                    is_check = False
                    break
                    
            return 'check' if is_check else 'call'
        elif action_code == 'cbr':
            # bet or raise
            is_bet = True
            current_street_actions = []
            for prev_action in previous_actions:
                prev_parts = prev_action.split()
                if prev_parts[0] == 'd' and prev_parts[1] == 'db':
                    current_street_actions = []
                elif prev_parts[0] != 'd':  
                    current_street_actions.append(prev_action)
                    
            for prev_action in current_street_actions:
                prev_parts = prev_action.split()
                if prev_parts[1] == 'cbr': 
                    is_bet = False
                    break
                    
            return 'bet' if is_bet else 'raise'
            
        return action_code

    def generate_sql_statements(self, hand_data: Dict) -> List[str]:
        sql_statements = []
        
        game_id = f"G{self.game_folder}"
        self.hand_counter += 1
        hand_id = f"H{self.game_folder}_{self.hand_counter}"
        
        # Insert Players
        for username in hand_data['players']:
            player_id = self.get_player_id(username)
            sql_statements.append(
                f"insert into Player (player_id, username, email, password, date_of_birth, country_of_birth, current_balance) values ('{player_id}', '{username}', '{username.lower()}@example.com', 'hashed_password', '1990-01-01', 'USA', {hand_data['starting_stacks'][0]});"
            )

        # Insert Game
        if self.hand_counter == 1:
            sql_statements.append(
                f"insert into Game (game_id, game_type, small_blind, big_blind, min_players, max_players) values ('{game_id}', {hand_data['variant']}, {hand_data['blinds_or_straddles'][0]}, {hand_data['blinds_or_straddles'][1]}, 2, 6);"
            )

            # Insert Played_In_Game
            for i, (player, start_stack, end_stack) in enumerate(zip(
                hand_data['players'], 
                hand_data['starting_stacks'], 
                hand_data['finishing_stacks']
            )):
                player_id = self.get_player_id(player)
                sql_statements.append(
                    f"insert into Played_In_Game (player_id, game_id, buy_in_amount, seat_number, final_stack) values ('{player_id}', '{game_id}', {start_stack}, {i+1}, {end_stack});"
                )

        # Insert Hand
        pot_size = calculate_pot_size(hand_data['actions'], hand_data['blinds_or_straddles'])
        dealer_pos = self.get_and_rotate_dealer()
        sql_statements.append(
            f"insert into Hand (hand_id, game_id, dealer_position, pot_size) values ('{hand_id}', '{game_id}', {dealer_pos}, {pot_size});"
        )

        # Process actions to get player hole cards and community cards
        hole_cards = {}
        community_cards = []
        
        for action in hand_data['actions']:
            parts = action.split()
            if parts[0] == 'd':
                if parts[1] == 'dh':
                    player = parts[2]
                    cards = parts[3]
                    hole_cards[player] = (cards[:2], cards[2:])
                elif parts[1] == 'db':
                    new_cards = [parts[2][i:i+2] for i in range(0, len(parts[2]), 2)]
                    community_cards.extend(new_cards)

        # Insert Community_Cards
        for i, card in enumerate(community_cards):
            card_id = f"{card}"
            street = 'flop' if i < 3 else 'turn' if i == 3 else 'river'
            sql_statements.append(
                f"insert into Community_Cards (hand_id, card_id, street) values ('{hand_id}', '{card_id}', '{street}');"
            )

        # Insert Played_In_Hand
        for player_key, cards in hole_cards.items():
            player_num = int(player_key[1])
            player_id = self.get_player_id(hand_data['players'][player_num-1])
            card1_id = f"{cards[0]}"
            card2_id = f"{cards[1]}"
            amount_won = hand_data['finishing_stacks'][player_num-1] - hand_data['starting_stacks'][player_num-1]
            
            sql_statements.append(
                f"insert into Played_In_Hand (player_id, hand_id, card1_id, card2_id, final_result, hand_rank, amount_won) values ('{player_id}', '{hand_id}', '{card1_id}', '{card2_id}', 'folded', null, {amount_won});"
            )

        # Insert Action
        action_order = 1
        actions_so_far = []
        for i, action in enumerate(hand_data['actions']):
            parts = action.split()
            if parts[0] not in ['d']:
                if parts[1] == 'sm':  # Skip showdown/muck actions
                    continue
                    
                player = int(parts[0][1])
                player_id = self.get_player_id(hand_data['players'][player-1])
                current_street = self.determine_street(hand_data['actions'], i)
                action_type = self.determine_action_type(action, current_street, actions_so_far)
                amount = parts[2] if len(parts) > 2 else 'null'
                self.action_counter += 1
                action_id = f"A{self.game_folder}_{self.action_counter}"
                
                sql_statements.append(
                    f"insert into Action (action_id, hand_id, player_id, street, action_type, amount, action_order) values ('{action_id}', '{hand_id}', '{player_id}', '{current_street}', '{action_type}', {amount}, {action_order});"
                )
                action_order += 1
            
            actions_so_far.append(action)

        return sql_statements


def process_directory(directory_path: str, output_file: str = "poker_hands.sql"):
    with open(output_file, 'w') as out_file:
        out_file.write("-- Poker Hands SQL Insert Statements\n")
        
        folders = []
        for folder_name in os.listdir(directory_path):
            folder_path = os.path.join(directory_path, folder_name)
            if os.path.isdir(folder_path):
                try:
                    folders.append((int(folder_name), folder_name))
                except ValueError:
                    continue
        
        folders.sort(key=lambda x: x[0])
        
        for _, folder_name in folders:
            folder_path = os.path.join(directory_path, folder_name)
            try:
                game_id = int(folder_name)
                sql_generator = SQLGenerator(game_id)
                
                out_file.write(f"\n-- Processing game {game_id} from folder {folder_name}\n")
                print(f"Processing game {game_id} from folder {folder_name}")
                
                phh_files = []
                for f in os.listdir(folder_path):
                    if f.endswith('.phh'):
                        try:
                            file_num = int(f[:-4])
                            phh_files.append((file_num, f))
                        except ValueError:
                            continue
                
                phh_files.sort(key=lambda x: x[0])
                
                for _, file_name in phh_files:
                    file_path = os.path.join(folder_path, file_name)
                    try:
                        hand_data = parse_text_file(file_path)
                        sql_statements = sql_generator.generate_sql_statements(hand_data)
                        
                        out_file.write(f"\n-- Hand from {file_name}\n")
                        for statement in sql_statements:
                            out_file.write(statement + "\n")
                            
                        print(f"  Processed hand from {file_name}")
                        
                    except Exception as e:
                        error_msg = f"Error processing {file_name}: {str(e)}\n"
                        out_file.write(f"\n-- {error_msg}")
                        print(error_msg)
                        import traceback
                        print(traceback.format_exc())
                        
            except ValueError:
                print(f"Skipping folder {folder_name} - not a valid game ID")
                continue
    
    print(f"\nProcessing complete. SQL statements saved to {output_file}")


def main():
    directory_path = '../poker_hands'
    output_file = '../poker_hands.sql'
    
    if not os.path.exists(directory_path):
        print(f"Error: Directory '{directory_path}' not found")
        return
        
    process_directory(directory_path, output_file)


if __name__ == "__main__":
    main()