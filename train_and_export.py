# train_and_export.py
"""
Ré-entraîne le CFR sur le Kuhn Poker et exporte la stratégie moyenne apprise
dans strategy.json, utilisé ensuite par l'application Streamlit (app.py).

Ce script n'a pas besoin d'être relancé pour utiliser l'appli, strategy.json
est déjà fourni dans le repo. Il sert si tu veux ré-entraîner avec plus
d'itérations, ou vérifier que les chiffres sont reproductibles.
"""

import json
import random
from core.kuhn_cfr import KuhnCFRTrainer

def export_strategy(num_iterations=200_000, seed=0, output_path="strategy.json"):
    random.seed(seed)
    trainer = KuhnCFRTrainer()
    average_game_value = trainer.train(num_iterations)

    output = {}
    for key, info_set in trainer.info_sets.items():
        card = key[0]
        history = key[1:] if len(key) > 1 else "root"
        output.setdefault(card, {})[history] = info_set.get_average_strategy()

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Valeur moyenne du jeu pour le premier joueur : {average_game_value:.4f}")
    print(f"(Valeur théorique connue : -1/18 = {-1/18:.4f})")
    print(f"Stratégie exportée dans {output_path}")

if __name__ == "__main__":
    export_strategy()
