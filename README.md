# Kuhn Poker GTO Trainer

Une IA qui apprend une stratégie de poker optimale par elle-même, via l'algorithme Counterfactual Regret Minimization (CFR), et une appli interactive pour jouer contre elle et comparer chacune de ses décisions à la recommandation théorique optimale.

CFR est l'algorithme qui est derrière les meilleurs bots de poker au monde (Libratus, Pluribus). Ce projet l'implémente à la main sur le Kuhn Poker, une version miniature du poker (3 cartes, 2 joueurs, un seul tour de mise) suffisamment petite pour que la stratégie optimale soit calculable et vérifiable mathématiquement, mais qui garde les mêmes mécanismes fondamentaux que le vrai poker : bluff, semi-bluff, gestion du risque en information imparfaite.

## Démo

Lien vers la démo live : à ajouter après déploiement (voir section Déploiement plus bas).

## Comment ça marche

1. **`core/poker_hand_evaluator.py`** : évalue et compare des mains de poker classiques (paire, couleur, full, etc). Première brique du projet, sans lien direct avec le Kuhn Poker, mais qui pose les bases de manipulation de cartes en Python.
2. **`core/poker_equity_calculator.py`** : calcule par simulation Monte Carlo la probabilité de gagner d'une main de poker classique contre une main aléatoire.
3. **`core/kuhn_cfr.py`** : implémentation de l'algorithme CFR. Le principe : à chaque itération, l'IA joue contre elle-même, calcule pour chaque décision le regret de ne pas avoir joué autrement (le "counterfactual regret"), et ajuste sa stratégie pour minimiser ce regret au fil du temps. Répété sur des centaines de milliers d'itérations, la stratégie moyenne obtenue converge vers un équilibre de Nash, une stratégie qu'aucun adversaire ne peut exploiter.
4. **`train_and_export.py`** : lance l'entraînement CFR et exporte la stratégie apprise dans `strategy.json`.
5. **`app.py`** : l'appli Streamlit qui charge cette stratégie et permet de jouer contre elle, avec affichage en direct de la recommandation optimale à chaque décision.

## Résultat de l'entraînement

Avec 200 000 itérations, l'algorithme converge vers une valeur de jeu de -0.0611 pour le joueur qui parle en premier, très proche de la valeur théorique connue de -1/18 (-0.0556). Ça confirme que l'implémentation trouve bien la stratégie optimale, pas juste une approximation grossière.

La stratégie apprise retrouve des comportements connus en théorie des jeux :
- Avec la meilleure carte (Roi), l'IA mise dans la grande majorité des cas.
- Avec la pire carte (Valet), elle checke surtout, mais bluffe environ une fois sur cinq.
- Avec la carte intermédiaire (Dame), elle suit environ une fois sur deux quand l'adversaire mise après un check, exactement ce qu'il faut faire pour ne pas être exploitable par les bluffs sans pour autant sur-suivre.

## Installation locale

```bash
git clone <url-de-ton-repo>
cd kuhn-poker-gto
pip install -r requirements.txt
streamlit run app.py
```

L'appli s'ouvre automatiquement dans le navigateur à `http://localhost:8501`.

## Ré-entraîner le modèle

`strategy.json` est déjà fourni, donc ce n'est pas nécessaire pour utiliser l'appli. Pour ré-entraîner (par exemple avec plus d'itérations) :

```bash
python train_and_export.py
```

## Auteur

Charles Dresco
