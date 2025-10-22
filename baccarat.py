
#!/usr/bin/env python3
"""
Terminal Baccarat (Punto Banco) game

How to run:
    python3 baccarat_terminal.py

Controls:
 - Choose bet type: player / banker / tie (or p / b / t)
 - Enter bet amount (integer)
 - Press Enter to play the round
 - Type 'q' or 'quit' to exit the game

Rules implemented:
 - Uses 8 decks (standard shoe)
 - Card values: A=1, 2-9 face value, 10/J/Q/K=0
 - Hand total = units digit of sum (e.g., 15 -> 5)
 - Standard Punto Banco third-card rules for Player and Banker
 - Banker wins pay 95% (5% commission), Player wins pay 1:1, Tie pays 8:1
 - Reshuffles when shoe has fewer than 6 cards remaining
"""

import random
import sys

DECKS = 8
RESHUFFLE_THRESHOLD = 6  # reshuffle when fewer than this many cards remain

def create_shoe(decks=DECKS):
    ranks = ['A','2','3','4','5','6','7','8','9','10','J','Q','K']
    single_deck = ranks * 4
    shoe = single_deck * decks
    random.shuffle(shoe)
    return shoe

def card_value(rank):
    if rank == 'A':
        return 1
    if rank in ('10','J','Q','K'):
        return 0
    return int(rank)

def hand_total(hand):
    total = sum(card_value(c) for c in hand) % 10
    return total

def draw(shoe):
    if not shoe:
        raise ValueError("The shoe is empty. Should reshuffle before drawing.")
    return shoe.pop(0)

def player_draws(player_total):
    # Player draws a third card if total 0-5, stands on 6-7, natural on 8-9 handled outside
    return player_total <= 5

def banker_draws(bank_total, player_third_card):
    # If player did not draw a third card, banker draws on 0-5, stands on 6-7.
    if player_third_card is None:
        return bank_total <= 5
    # If player drew a third card, use the complex rules
    p3 = card_value(player_third_card)
    if bank_total <= 2:
        return True
    if bank_total == 3:
        return p3 != 8
    if bank_total == 4:
        return 2 <= p3 <= 7
    if bank_total == 5:
        return 4 <= p3 <= 7
    if bank_total == 6:
        return p3 in (6,7)
    return False  # bank_total == 7 -> stand

def settle_bet(bet_type, bet_amount, winner):
    # winner: 'player', 'banker', 'tie'
    if winner == 'tie':
        if bet_type == 'tie':
            # Tie pays 8:1 typically (some casinos 9:1) — we'll use 8:1
            return bet_amount * 8
        else:
            # push for player/banker bets on tie -> return bet (no win, no loss)
            return 0  # indicate push (handled by caller)
    elif winner == 'player':
        if bet_type == 'player':
            return bet_amount  # 1:1 profit
        elif bet_type == 'banker':
            return -bet_amount  # lost bet
    elif winner == 'banker':
        if bet_type == 'banker':
            # Banker wins pay 0.95 (5% commission)
            return int(round(bet_amount * 0.95))
        elif bet_type == 'player':
            return -bet_amount
    return -bet_amount  # default lost bet

def print_hand(label, hand):
    cards = ' '.join(hand)
    print(f"{label}: {cards}  -> total {hand_total(hand)}")

def play_round(shoe):
    # Deal initial four cards: Player, Banker, Player, Banker
    player = [draw(shoe), draw(shoe)]
    banker = [draw(shoe), draw(shoe)]
    p_total = hand_total(player)
    b_total = hand_total(banker)

    # Naturals check
    if p_total in (8,9) or b_total in (8,9):
        # Natural - no more cards
        player_third = None
        banker_third = None
    else:
        # Player third-card rule
        player_third = None
        if player_draws(p_total):
            player_third = draw(shoe)
            player.append(player_third)
        # Recompute totals modulo 10 for third-card evaluation for banker
        p_total = hand_total(player)
        # Banker third-card rule depends on whether player drew
        banker_third = None
        if banker_draws(b_total, player_third):
            banker_third = draw(shoe)
            banker.append(banker_third)

    p_total = hand_total(player)
    b_total = hand_total(banker)

    # Decide winner
    if p_total > b_total:
        winner = 'player'
    elif b_total > p_total:
        winner = 'banker'
    else:
        winner = 'tie'

    return {
        'player_hand': player,
        'banker_hand': banker,
        'player_total': p_total,
        'banker_total': b_total,
        'winner': winner,
        'player_third': player_third,
        'banker_third': banker_third
    }

def prompt_bet(bankroll):
    while True:
        choice = input("Bet on (player/banker/tie) [p/b/t] (or 'q' to quit): ").strip().lower()
        if choice in ('q','quit'):
            return None, None
        mapping = {'p':'player','b':'banker','t':'tie','player':'player','banker':'banker','tie':'tie'}
        if choice in mapping:
            bet_type = mapping[choice]
            break
        print("Invalid choice. Please enter p, b, or t.")

    while True:
        try:
            amt_str = input(f"Enter bet amount (bankroll ${bankroll}): ").strip()
            if amt_str.lower() in ('q','quit'):
                return None, None
            amt = int(amt_str)
            if amt <= 0:
                print("Bet must be positive.")
                continue
            if amt > bankroll:
                print("You don't have enough bankroll for that bet.")
                continue
            return bet_type, amt
        except ValueError:
            print("Enter a whole number amount (e.g., 50).")

def main():
    print("Welcome to Terminal Baccarat (Punto Banco)\n")
    shoe = create_shoe()
    bankroll = 1000  # starting bankroll
    round_no = 0

    while True:
        if len(shoe) < RESHUFFLE_THRESHOLD:
            print("\n*** Reshuffling the shoe... ***\n")
            shoe = create_shoe()

        print(f"\nBankroll: ${bankroll} | Cards left in shoe: {len(shoe)}")
        bet_type, bet_amount = prompt_bet(bankroll)
        if bet_type is None:
            print("Thanks for playing. Goodbye!")
            break

        round_no += 1
        print(f"\n--- Round {round_no} ---")
        result = play_round(shoe)
        print_hand("Player", result['player_hand'])
        print_hand("Banker", result['banker_hand'])

        winner = result['winner']
        if winner == 'tie':
            print("Result: TIE")
            # Tie handling: bets on tie win 8:1, player/banker push (bet returned)
            if bet_type == 'tie':
                payout = settle_bet(bet_type, bet_amount, 'tie')
                bankroll += payout
                print(f"You won ${payout} on a tie bet!")
            else:
                print("Push on player/banker bet (bet returned).")
        elif winner == 'player':
            print("Result: PLAYER wins")
            payout = settle_bet(bet_type, bet_amount, 'player')
            if payout > 0:
                bankroll += payout
                print(f"You won ${payout}!")
            else:
                bankroll -= bet_amount
                print(f"You lost ${bet_amount}.")
        elif winner == 'banker':
            print("Result: BANKER wins")
            if bet_type == 'banker':
                win = settle_bet(bet_type, bet_amount, 'banker')
                bankroll += win
                print(f"You won ${win} (after 5% commission).")
            else:
                bankroll -= bet_amount
                print(f"You lost ${bet_amount}.")

        # Prevent negative bankroll display (bankrupt)
        if bankroll <= 0:
            print("\nYou're out of money. Game over.")
            break

        # quick pause between rounds
        cont = input("\nPlay another round? (Enter to continue, 'q' to quit): ").strip().lower()
        if cont in ('q','quit'):
            print("Thanks for playing. Goodbye!")
            break

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted. Goodbye.")
