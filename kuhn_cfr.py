# kuhn_cfr.py
"""
Implémentation de Counterfactual Regret Minimization (CFR) sur le Kuhn Poker.

Règles du Kuhn Poker :
- 3 cartes : Valet (1), Dame (2), Roi (3)
- 2 joueurs, chacun ante 1 jeton, puis reçoit une carte cachée
- Le joueur 1 parle en premier : il peut checker ('p' pour pass) ou miser ('b' pour bet)
- Si check puis bet, l'autre joueur peut suivre ou se coucher
- Si mise directe, l'autre joueur peut suivre ou se coucher
- À showdown, la carte la plus haute gagne le pot

On représente une partie par son "historique", une chaîne de caractères comme
"pb" (joueur 1 check, joueur 2 mise). Chaque combinaison (carte du joueur, historique)
est une "information set" différente, pour laquelle on va apprendre une stratégie.
"""

import random

PASS = 0  # check ou fold, selon le contexte
BET = 1   # mise ou suivre, selon le contexte
NUM_ACTIONS = 2
ACTION_LABELS = ['p', 'b']


class InfoSet:
    """
    Stocke les regrets accumulés et la stratégie moyenne pour une information set donnée.
    """
    def __init__(self):
        self.regret_sum = [0.0, 0.0]      # regret accumulé pour chaque action
        self.strategy_sum = [0.0, 0.0]    # somme pondérée des stratégies jouées (pour la moyenne finale)

    def get_current_strategy(self, realization_weight):
        """
        Calcule la stratégie actuelle à partir des regrets positifs accumulés
        (règle du "regret matching"), puis met à jour la moyenne.
        """
        normalizing_sum = sum(max(r, 0.0) for r in self.regret_sum)
        strategy = [0.0, 0.0]
        for a in range(NUM_ACTIONS):
            if normalizing_sum > 0:
                strategy[a] = max(self.regret_sum[a], 0.0) / normalizing_sum
            else:
                strategy[a] = 0.5  # au tout début, aucun regret, on part à 50/50
            self.strategy_sum[a] += realization_weight * strategy[a]
        return strategy

    def get_average_strategy(self):
        """
        Retourne la stratégie moyenne sur toutes les itérations, c'est celle-ci
        qui converge vers l'équilibre, pas la stratégie d'une itération isolée.
        """
        total = sum(self.strategy_sum)
        if total > 0:
            return [s / total for s in self.strategy_sum]
        return [0.5, 0.5]


class KuhnCFRTrainer:
    def __init__(self):
        self.info_sets = {}  # clé: "carte" + "historique" -> InfoSet

    def get_info_set(self, key):
        if key not in self.info_sets:
            self.info_sets[key] = InfoSet()
        return self.info_sets[key]

    def cfr(self, cards, history, prob_reach_p0, prob_reach_p1):
        """
        Parcourt récursivement l'arbre du jeu pour une donne de cartes fixée,
        et retourne l'utilité (le gain espéré) pour le joueur dont c'est le tour.

        prob_reach_p0 et prob_reach_p1 sont les probabilités que chaque joueur
        ait joué, jusqu'ici, exactement les actions de cet historique. Elles
        servent à pondérer correctement les regrets (un joueur ne doit pas
        "apprendre" sur des situations que l'adversaire ne permettrait jamais
        d'atteindre).
        """
        plays = len(history)
        player = plays % 2       # à qui de jouer
        opponent = 1 - player

        # --- Cas terminaux : la partie est finie, on calcule directement le gain ---
        if plays > 1:
            player_card_is_higher = cards[player] > cards[opponent]

            if history[-1] == 'p' and history != 'pp':
                # L'adversaire vient de se coucher après une mise : le joueur actuel gagne l'ante adverse
                return 1.0
            if history == 'pp':
                # Personne n'a misé, showdown direct pour 1 jeton chacun
                return 1.0 if player_card_is_higher else -1.0
            if history[-2:] == 'bb':
                # Mise suivie : showdown pour 2 jetons chacun
                return 2.0 if player_card_is_higher else -2.0

        # --- Cas non terminal : on regarde la stratégie actuelle et on récurse ---
        info_set_key = str(cards[player]) + history
        info_set = self.get_info_set(info_set_key)

        reach_prob_of_current_player = prob_reach_p0 if player == 0 else prob_reach_p1
        strategy = info_set.get_current_strategy(reach_prob_of_current_player)

        action_utilities = [0.0, 0.0]
        node_utility = 0.0

        for a in range(NUM_ACTIONS):
            next_history = history + ACTION_LABELS[a]
            if player == 0:
                # Le signe moins vient du fait que l'utilité de l'adversaire
                # est l'opposée de la nôtre dans un jeu à somme nulle comme celui-ci
                action_utilities[a] = -self.cfr(cards, next_history, prob_reach_p0 * strategy[a], prob_reach_p1)
            else:
                action_utilities[a] = -self.cfr(cards, next_history, prob_reach_p0, prob_reach_p1 * strategy[a])
            node_utility += strategy[a] * action_utilities[a]

        # --- Mise à jour des regrets ---
        # Le regret de l'action a, c'est la différence entre ce qu'elle aurait rapporté
        # et ce que la stratégie actuelle rapporte en moyenne, pondérée par la probabilité
        # que l'ADVERSAIRE ait permis d'atteindre cette situation.
        opponent_reach_prob = prob_reach_p1 if player == 0 else prob_reach_p0
        for a in range(NUM_ACTIONS):
            regret = action_utilities[a] - node_utility
            info_set.regret_sum[a] += opponent_reach_prob * regret

        return node_utility

    def train(self, num_iterations):
        """
        Lance l'entraînement : à chaque itération, on tire une donne de cartes
        au hasard et on parcourt tout l'arbre du jeu pour cette donne.
        """
        cards = [1, 2, 3]
        total_utility = 0.0

        for _ in range(num_iterations):
            random.shuffle(cards)
            total_utility += self.cfr(cards, "", 1.0, 1.0)

        return total_utility / num_iterations


CARD_NAMES = {1: "Valet", 2: "Dame", 3: "Roi"}


def print_strategies(trainer):
    """Affiche la stratégie moyenne apprise pour chaque information set, de façon lisible."""
    print("\nStratégies moyennes apprises (probabilité de check/fold, probabilité de bet/call) :\n")
    for key in sorted(trainer.info_sets.keys(), key=lambda k: (k[1:], k[0])):
        card = int(key[0])
        history = key[1:] if len(key) > 1 else "(début)"
        avg_strategy = trainer.info_sets[key].get_average_strategy()
        print(f"Carte = {CARD_NAMES[card]:5} | historique = {history:8} "
              f"-> check/fold: {avg_strategy[0]*100:5.1f}%  bet/call: {avg_strategy[1]*100:5.1f}%")


if __name__ == "__main__":
    random.seed(0)

    trainer = KuhnCFRTrainer()
    num_iterations = 200_000

    print(f"Entraînement de CFR sur {num_iterations} itérations...\n")
    average_game_value = trainer.train(num_iterations)

    print(f"Valeur moyenne du jeu pour le joueur qui parle en premier : {average_game_value:.4f}")
    print("(La valeur théorique connue du Kuhn Poker est -1/18 = -0.0556 pour le premier joueur,")
    print(" ce qui signifie que parler en premier est légèrement désavantageux, comme au poker réel.)")

    print_strategies(trainer)
