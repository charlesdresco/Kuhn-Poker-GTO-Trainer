# poker_equity_calculator.py
"""
Calculateur d'équité au poker par simulation Monte Carlo.

L'équité d'une main, c'est la probabilité qu'elle gagne (ou fasse égalité)
si la partie était jouée jusqu'au bout. Comme calculer ça exactement demande
d'examiner un nombre énorme de combinaisons de cartes restantes, on préfère
l'estimer en simulant des milliers de parties aléatoires.

Ce fichier réutilise poker_hand_evaluator.py pour savoir qui gagne chaque
partie simulée.
"""

import random
from poker_hand_evaluator import best_hand, card_to_str

# ---------------------------------------------------------
# 1. Construire un jeu de 52 cartes
# ---------------------------------------------------------

def build_deck():
    """Retourne la liste complète des 52 cartes."""
    suits = ['P', 'C', 'D', 'T']
    values = list(range(2, 15))  # 2 à 14 (14 = As)
    return [(v, s) for v in values for s in suits]


def remove_known_cards(deck, known_cards):
    """Retire du deck les cartes déjà visibles (main du joueur, cartes communes)."""
    return [card for card in deck if card not in known_cards]


# ---------------------------------------------------------
# 2. Simuler une seule partie aléatoire
# ---------------------------------------------------------

def simulate_one_hand(hero_cards, community_cards, num_opponents, remaining_deck):
    """
    Complète aléatoirement les cartes manquantes (adversaires + board),
    puis détermine si le héros gagne, perd, ou fait égalité.

    Retourne 'win', 'tie' ou 'loss'.
    """
    # On mélange une copie du deck restant pour piocher aléatoirement
    shuffled = remaining_deck.copy()
    random.shuffle(shuffled)

    nb_missing_community = 5 - len(community_cards)
    nb_cards_needed = nb_missing_community + 2 * num_opponents

    drawn = shuffled[:nb_cards_needed]
    missing_community = drawn[:nb_missing_community]
    opponents_cards = [
        drawn[nb_missing_community + i * 2: nb_missing_community + i * 2 + 2]
        for i in range(num_opponents)
    ]

    full_community = community_cards + missing_community

    hero_score = best_hand(hero_cards + full_community)
    opponents_scores = [best_hand(opp + full_community) for opp in opponents_cards]

    best_opponent_score = max(opponents_scores)

    if hero_score > best_opponent_score:
        return 'win'
    elif hero_score == best_opponent_score:
        return 'tie'
    else:
        return 'loss'


# ---------------------------------------------------------
# 3. Lancer plusieurs simulations et calculer les probabilités
# ---------------------------------------------------------

def calculate_equity(hero_cards, community_cards=None, num_opponents=1, num_simulations=10000):
    """
    Estime la probabilité de victoire, d'égalité et de défaite de hero_cards
    en simulant num_simulations parties aléatoires.
    """
    if community_cards is None:
        community_cards = []

    known_cards = hero_cards + community_cards
    deck = build_deck()
    remaining_deck = remove_known_cards(deck, known_cards)

    results = {'win': 0, 'tie': 0, 'loss': 0}

    for _ in range(num_simulations):
        outcome = simulate_one_hand(hero_cards, community_cards, num_opponents, remaining_deck)
        results[outcome] += 1

    total = sum(results.values())
    equity = {
        'win_pct': 100 * results['win'] / total,
        'tie_pct': 100 * results['tie'] / total,
        'loss_pct': 100 * results['loss'] / total,
    }
    return equity


# ---------------------------------------------------------
# 4. Exemples connus pour vérifier que les chiffres sont réalistes
# ---------------------------------------------------------

if __name__ == "__main__":
    random.seed(42)

    print("=== Calculateur d'équité Monte Carlo ===\n")

    # Exemple 1 : As-Roi assorti contre une main aléatoire, avant le flop
    hero = [(14, 'P'), (13, 'P')]
    print(f"Main héro : {card_to_str(hero[0])}, {card_to_str(hero[1])}")
    equity = calculate_equity(hero, num_opponents=1, num_simulations=20000)
    print(f"As-Roi assorti vs 1 main aléatoire : victoire {equity['win_pct']:.1f}%, "
          f"égalité {equity['tie_pct']:.1f}%, défaite {equity['loss_pct']:.1f}%")
    print("(Valeur connue attendue autour de 65% de victoires)\n")

    # Exemple 2 : Paire d'As contre paire de Rois, un classique "coup de dés" au poker
    hero = [(14, 'P'), (14, 'C')]
    villain_fixed_cards = [(13, 'D'), (13, 'T')]
    deck = build_deck()
    remaining = remove_known_cards(deck, hero + villain_fixed_cards)

    results = {'win': 0, 'tie': 0, 'loss': 0}
    num_simulations = 20000
    for _ in range(num_simulations):
        shuffled = remaining.copy()
        random.shuffle(shuffled)
        community = shuffled[:5]
        hero_score = best_hand(hero + community)
        villain_score = best_hand(villain_fixed_cards + community)
        if hero_score > villain_score:
            results['win'] += 1
        elif hero_score == villain_score:
            results['tie'] += 1
        else:
            results['loss'] += 1

    total = sum(results.values())
    print(f"Paire d'As vs Paire de Rois (heads-up) : victoire {100*results['win']/total:.1f}%, "
          f"égalité {100*results['tie']/total:.1f}%, défaite {100*results['loss']/total:.1f}%")
    print("(Valeur connue attendue autour de 80-82% de victoires pour la paire d'As)\n")

    # Exemple 3 : équité après un flop donné
    hero = [(10, 'P'), (9, 'P')]
    flop = [(8, 'P'), (7, 'C'), (2, 'D')]  # tirage quinte ouverte
    print(f"Main héro : {card_to_str(hero[0])}, {card_to_str(hero[1])}, avec un flop {[card_to_str(c) for c in flop]}")
    equity = calculate_equity(hero, community_cards=flop, num_opponents=1, num_simulations=20000)
    print(f"Tirage quinte ouverte vs 1 main aléatoire après le flop : victoire {equity['win_pct']:.1f}%, "
          f"égalité {equity['tie_pct']:.1f}%, défaite {equity['loss_pct']:.1f}%")
