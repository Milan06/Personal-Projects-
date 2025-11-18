
#!/usr/bin/env python3
"""
Terminal Blackjack game
Features:
 - Single player vs dealer
 - Betting with balance
 - Hit / Stand / Double Down (one-card double)
 - Blackjack (natural) pays 3:2
 - Dealer hits on soft 16 (dealer stands on 17+ - standard rules)
 - Input-validated, friendly prompts
Author: ChatGPT (GPT-5 Thinking mini)
"""

import random
import sys
import textwrap

SUITS = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

def create_deck(num_decks=6):
    deck = []
    for _ in range(num_decks):
        for s in SUITS:
            for r in RANKS:
                deck.append((r, s))
    random.shuffle(deck)
    return deck

def card_str(card):
    rank, suit = card
    suit_symbol = {'Hearts':'♥','Diamonds':'♦','Clubs':'♣','Spades':'♠'}[suit]
    return f"{rank}{suit_symbol}"

def hand_value(hand):
    # return (best_value, is_soft)
    value = 0
    aces = 0
    for r, _ in hand:
        if r in ['J','Q','K']:
            value += 10
        elif r == 'A':
            aces += 1
            value += 11  # count as 11 for now
        else:
            value += int(r)
    # downgrade aces from 11 to 1 as needed
    while value > 21 and aces:
        value -= 10
        aces -= 1
    is_soft = any(r == 'A' for r, _ in hand) and value <= 21 and any(r == 'A' for r, _ in hand) and value - 10 >= 11
    return value, is_soft

def is_blackjack(hand):
    v, _ = hand_value(hand)
    return v == 21 and len(hand) == 2

def display_hands(player_hand, dealer_hand, hide_dealer_card=True):
    ph = ' '.join(card_str(c) for c in player_hand)
    if hide_dealer_card:
        dh = f"{card_str(dealer_hand[0])} ??"
    else:
        dh = ' '.join(card_str(c) for c in dealer_hand)
    print(f"\nDealer: {dh}")
    print(f"You:    {ph}  ({hand_value(player_hand)[0]})\n")

def take_bet(balance):
    while True:
        try:
            bet = input(f"You have ${balance}. Enter your bet: $").strip()
            if bet.lower() in ('q','quit','exit'):
                return None
            bet = float(bet)
            if bet <= 0:
                print("Bet must be positive.")
            elif bet > balance:
                print("You don't have enough for that bet.")
            else:
                # normalize to 2 decimal places and cents
                bet = round(bet, 2)
                return bet
        except ValueError:
            print("Enter a valid number (or 'q' to quit).")

def player_turn(deck, hand, dealer_upcard, can_double):
    while True:
        value, _ = hand_value(hand)
        if value > 21:
            print("You busted!")
            return 'bust', hand
        options = ['(H)it', '(S)tand']
        if can_double and len(hand) == 2:
            options.append('(D)ouble down')
        print("Options: " + ' / '.join(options))
        choice = input("Choose: ").strip().lower()
        if choice in ('h','hit'):
            hand.append(deck.pop())
            display_hands(hand, [dealer_upcard], hide_dealer_card=True)  # only show dealer upcard
            continue
        elif choice in ('s','stand'):
            return 'stand', hand
        elif choice in ('d','double','double down') and can_double and len(hand) == 2:
            return 'double', hand
        else:
            print("Invalid choice. Try again.")

def dealer_turn(deck, hand):
    # Dealer hits until 17 or higher; typical rule: dealer hits soft 16 and stands on soft 17.
    while True:
        value, is_soft = hand_value(hand)
        if value < 17:
            hand.append(deck.pop())
            continue
        # if value == 17 and is_soft: many casinos stand on soft 17; we'll stand on all 17s.
        break
    return hand

def settle_bet(player_hand, dealer_hand, bet):
    pv, _ = hand_value(player_hand)
    dv, _ = hand_value(dealer_hand)
    # check for blackjack
    if is_blackjack(player_hand) and not is_blackjack(dealer_hand):
        return bet * 1.5  # player wins 3:2 (profit)
    if is_blackjack(player_hand) and is_blackjack(dealer_hand):
        return 0  # push
    if pv > 21:
        return -bet
    if dv > 21:
        return bet
    if pv > dv:
        return bet
    if pv < dv:
        return -bet
    return 0  # push

def print_round_result(player_hand, dealer_hand, bet, net):
    pv, _ = hand_value(player_hand)
    dv, _ = hand_value(dealer_hand)
    print("\nFinal hands:")
    print("Dealer:", ' '.join(card_str(c) for c in dealer_hand), f"({dv})")
    print("You:   ", ' '.join(card_str(c) for c in player_hand), f"({pv})")
    if is_blackjack(player_hand) and not is_blackjack(dealer_hand):
        print(f"You got a Blackjack! You win ${bet * 1.5:.2f}.")
    elif net > 0:
        print(f"You win ${net:.2f}!")
    elif net < 0:
        print(f"You lose ${-net:.2f}.")
    else:
        print("Push (tie).")

def play_round(deck, balance):
    if len(deck) < 15:
        print("Reshuffling the shoe...")
        deck[:] = create_deck()
    bet = take_bet(balance)
    if bet is None:
        return None, balance, False  # signal quit
    # initial deal
    player_hand = [deck.pop(), deck.pop()]
    dealer_hand = [deck.pop(), deck.pop()]
    display_hands(player_hand, dealer_hand, hide_dealer_card=True)
    # check naturals
    if is_blackjack(player_hand) or is_blackjack(dealer_hand):
        display_hands(player_hand, dealer_hand, hide_dealer_card=False)
        net = settle_bet(player_hand, dealer_hand, bet)
        balance += net
        print_round_result(player_hand, dealer_hand, bet, net)
        return True, balance, True
    # player's turn
    action, _ = player_turn(deck, player_hand, dealer_hand[0], can_double=True)
    if action == 'bust':
        net = -bet
        balance += net
        print_round_result(player_hand, dealer_hand, bet, net)
        return True, balance, True
    elif action == 'double':
        # take one card, double bet, then stand
        if bet * 2 > balance:
            print("You don't have enough to double. Continuing as a hit.")
            player_hand.append(deck.pop())
        else:
            balance -= bet  # take extra bet upfront
            bet *= 2
            player_hand.append(deck.pop())
            print("After doubling, your hand:")
            display_hands(player_hand, dealer_hand, hide_dealer_card=True)
        # check bust
        if hand_value(player_hand)[0] > 21:
            net = -bet
            balance += net
            print_round_result(player_hand, dealer_hand, bet, net)
            return True, balance, True
    # stand -> dealer's turn
    dealer_hand = dealer_turn(deck, dealer_hand)
    display_hands(player_hand, dealer_hand, hide_dealer_card=False)
    net = settle_bet(player_hand, dealer_hand, bet)
    balance += net
    print_round_result(player_hand, dealer_hand, bet, net)
    return True, balance, True

def main():
    print(textwrap.dedent("""
    Welcome to Terminal Blackjack!
    Rules:
     - Blackjack pays 3:2.
     - Dealer stands on all 17s.
     - You can double down on your first two cards (one card dealt), if you have the money.
     - Enter 'q' for bets to quit the game.
    """))
    balance = 100.0
    deck = create_deck()
    while True:
        cont, balance, played = play_round(deck, balance)
        if cont is None:
            print("Thanks for playing! Final balance: ${:.2f}".format(balance))
            break
        if balance <= 0:
            print("You're out of money. Game over.")
            break
        # ask to continue
        while True:
            ans = input("\nPlay another hand? (Y/n): ").strip().lower()
            if ans in ('y','yes',''):
                break
            elif ans in ('n','no'):
                print("Thanks for playing! Final balance: ${:.2f}".format(balance))
                return
            else:
                print("Please enter y or n.")

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print('\\nGoodbye!')


