# poker_hand_evaluator.py
"""
Évaluateur de mains de poker.

Ce programme permet de :
1. Représenter des cartes à jouer
2. Déterminer la meilleure combinaison de 5 cartes parmi 5, 6 ou 7 cartes
3. Comparer deux mains entre elles pour savoir laquelle gagne

On utilise seulement itertools et collections, qui font partie de Python de base,
pas besoin d'installer quoi que ce soit.
"""

from itertools import combinations
from collections import Counter

# ---------------------------------------------------------
# 1. Représentation d'une carte
# ---------------------------------------------------------

# Une carte est représentée par un tuple (valeur, couleur).
# valeur : un entier de 2 à 14 (14 = As, 13 = Roi, 12 = Dame, 11 = Valet)
# couleur : une lettre parmi 'P' (Pique), 'C' (Coeur), 'D' (Carreau), 'T' (Trèfle)
# Exemple : (14, 'P') représente l'As de pique

RANK_NAMES = {14: "As", 13: "Roi", 12: "Dame", 11: "Valet"}
SUIT_NAMES = {'P': 'Pique', 'C': 'Coeur', 'D': 'Carreau', 'T': 'Trèfle'}

def rank_name(value):
    """Retourne le nom lisible d'une valeur de carte (ex: 14 -> 'As')."""
    return RANK_NAMES.get(value, str(value))

def card_to_str(card):
    """Convertit une carte en texte lisible, ex: (14, 'P') -> 'As de Pique'."""
    value, suit = card
    return f"{rank_name(value)} de {SUIT_NAMES[suit]}"


# ---------------------------------------------------------
# 2. Les catégories de mains, de la plus faible (0) à la plus forte (8)
# ---------------------------------------------------------

HAND_CATEGORIES = {
    0: "Carte haute",
    1: "Paire",
    2: "Double paire",
    3: "Brelan",
    4: "Suite",
    5: "Couleur",
    6: "Full",
    7: "Carré",
    8: "Suite couleur",
}


# ---------------------------------------------------------
# 3. Évaluer une main de EXACTEMENT 5 cartes
# ---------------------------------------------------------

def evaluate_5_cards(cards):
    """
    Prend exactement 5 cartes et retourne un score qui permet de la comparer
    à n'importe quelle autre main de 5 cartes.

    Le score est un tuple, par exemple (3, 10, 5) pour un brelan de 10 avec un kicker 5.
    Python compare les tuples élément par élément (comme on compare des mots dans un
    dictionnaire : on regarde la première lettre, puis la deuxième si égalité, etc).
    Donc plus le premier chiffre est grand, plus la main est forte.
    """
    values = sorted([c[0] for c in cards], reverse=True)
    suits = [c[1] for c in cards]

    # Counter compte combien de fois chaque valeur apparaît.
    # Ex: pour une main avec trois 10, Counter donne {10: 3, ...}
    value_counts = Counter(values)

    # On trie les valeurs d'abord par nombre d'occurrences (les brelans/paires en premier),
    # puis par valeur en cas d'égalité. Cela donne l'ordre exact utilisé pour comparer
    # deux mains de la même catégorie.
    counts_sorted = sorted(value_counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
    ordered_values = [v for v, count in counts_sorted]
    counts = [count for v, count in counts_sorted]

    is_flush = len(set(suits)) == 1  # toutes les cartes ont la même couleur

    # Vérifier la suite (straight), avec le cas particulier As-2-3-4-5
    unique_values = sorted(set(values), reverse=True)
    is_straight = False
    straight_high = None
    if len(unique_values) == 5:
        if unique_values[0] - unique_values[4] == 4:
            is_straight = True
            straight_high = unique_values[0]
        elif unique_values == [14, 5, 4, 3, 2]:  # As-2-3-4-5, la "petite suite"
            is_straight = True
            straight_high = 5

    if is_straight and is_flush:
        return (8, straight_high)

    if counts == [4, 1]:
        return (7, ordered_values[0], ordered_values[1])

    if counts == [3, 2]:
        return (6, ordered_values[0], ordered_values[1])

    if is_flush:
        return (5, *ordered_values)

    if is_straight:
        return (4, straight_high)

    if counts == [3, 1, 1]:
        return (3, *ordered_values)

    if counts == [2, 2, 1]:
        return (2, *ordered_values)

    if counts == [2, 1, 1, 1]:
        return (1, *ordered_values)

    return (0, *ordered_values)


# ---------------------------------------------------------
# 4. Trouver la meilleure main de 5 cartes parmi 5, 6 ou 7 cartes
# ---------------------------------------------------------

def best_hand(cards):
    """
    Prend une liste de 5, 6 ou 7 cartes (2 cartes en main + jusqu'à 5 cartes communes)
    et retourne le meilleur score possible en testant toutes les combinaisons de 5 cartes.

    Avec 7 cartes il y a exactement 21 façons de choisir 5 cartes (calcul combinatoire
    C(7,5) = 21), donc on peut se permettre de toutes les tester une par une.
    """
    if len(cards) < 5:
        raise ValueError("Il faut au moins 5 cartes pour évaluer une main.")

    best_score = None
    for combo in combinations(cards, 5):
        score = evaluate_5_cards(combo)
        if best_score is None or score > best_score:
            best_score = score
    return best_score


def describe_hand(score):
    """Retourne une description lisible d'un score, ex: 'Brelan (score complet: (3, 10, 5, 2))'."""
    category = HAND_CATEGORIES[score[0]]
    return f"{category} (score complet: {score})"


def compare_hands(cards_1, cards_2):
    """
    Compare deux mains (chacune avec 5 à 7 cartes) et dit laquelle gagne.
    Retourne 1 si la main 1 gagne, 2 si la main 2 gagne, 0 en cas d'égalité parfaite.
    """
    score_1 = best_hand(cards_1)
    score_2 = best_hand(cards_2)

    if score_1 > score_2:
        return 1
    elif score_2 > score_1:
        return 2
    else:
        return 0


# ---------------------------------------------------------
# 5. Tests pour vérifier que tout fonctionne correctement
# ---------------------------------------------------------

if __name__ == "__main__":
    print("=== Tests de l'évaluateur de mains ===\n")

    # Test 1 : une paire d'As doit battre une paire de Rois
    main_1 = [(14, 'P'), (14, 'C'), (2, 'D'), (5, 'T'), (9, 'P')]
    main_2 = [(13, 'P'), (13, 'C'), (2, 'C'), (5, 'D'), (9, 'D')]
    resultat = compare_hands(main_1, main_2)
    print(f"Paire d'As vs Paire de Rois -> gagnant: main {resultat}")
    assert resultat == 1

    # Test 2 : une couleur doit battre une suite
    main_flush = [(2, 'P'), (5, 'P'), (7, 'P'), (9, 'P'), (12, 'P')]
    main_straight = [(3, 'C'), (4, 'D'), (5, 'T'), (6, 'P'), (7, 'C')]
    resultat = compare_hands(main_flush, main_straight)
    print(f"Couleur vs Suite -> gagnant: main {resultat}")
    assert resultat == 1

    # Test 3 : la petite suite As-2-3-4-5 doit être reconnue comme une suite
    main_wheel = [(14, 'P'), (2, 'C'), (3, 'D'), (4, 'T'), (5, 'P')]
    score = best_hand(main_wheel)
    print(f"Main As-2-3-4-5 -> {describe_hand(score)}")
    assert score[0] == 4

    # Test 4 : meilleure main parmi 7 cartes, avec une quinte flush royale cachée dedans
    main_avec_communes = [(14, 'P'), (13, 'P'), (12, 'P'), (11, 'P'), (10, 'P'), (2, 'C'), (3, 'D')]
    score = best_hand(main_avec_communes)
    print(f"7 cartes contenant une quinte flush royale -> {describe_hand(score)}")
    assert score[0] == 8

    # Test 5 : un full doit battre une couleur
    main_full = [(9, 'P'), (9, 'C'), (9, 'D'), (4, 'T'), (4, 'P')]
    main_couleur = [(2, 'C'), (6, 'C'), (8, 'C'), (10, 'C'), (13, 'C')]
    resultat = compare_hands(main_full, main_couleur)
    print(f"Full vs Couleur -> gagnant: main {resultat}")
    assert resultat == 1

    print("\nTous les tests sont passés avec succès.")
