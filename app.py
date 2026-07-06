# app.py
"""
Application Streamlit : joue une main de Kuhn Poker contre une IA entraînée
par Counterfactual Regret Minimization (CFR), et affiche à chaque décision
la recommandation théorique optimale (GTO) calculée par l'algorithme.

Pour lancer en local :
    pip install -r requirements.txt
    streamlit run app.py
"""

import json
import random

import streamlit as st

st.set_page_config(page_title="Kuhn Poker - IA entraînée par CFR", page_icon=":spades:")

with open("strategy.json") as f:
    STRATEGY = json.load(f)

CARD_NAMES = {1: "Valet", 2: "Dame", 3: "Roi"}


def get_strategy(card, key):
    return STRATEGY[str(card)][key]


def deal_new_hand():
    cards = [1, 2, 3]
    random.shuffle(cards)
    st.session_state.human_card = cards[0]
    st.session_state.bot_card = cards[1]
    st.session_state.history = ""
    st.session_state.feed = ["Nouvelle main distribuée. À vous de parler."]
    st.session_state.stage = "human_turn"
    st.session_state.last_recommendation = None


def init_state():
    if "human_chips" not in st.session_state:
        st.session_state.human_chips = 0
        st.session_state.bot_chips = 0
        st.session_state.hands_played = 0
        st.session_state.gto_aligned = 0
        st.session_state.gto_total = 0
        deal_new_hand()


def human_action(action, key):
    rec = get_strategy(st.session_state.human_card, key)
    st.session_state.gto_total += 1
    recommended = "b" if rec[1] > rec[0] else "p"
    if action == recommended:
        st.session_state.gto_aligned += 1

    if action == "p":
        label = "Vous checkez." if key == "root" else "Vous vous couchez."
    else:
        label = "Vous misez." if key == "root" else "Vous suivez."

    st.session_state.feed.append(label)
    st.session_state.history += action
    st.session_state.last_recommendation = (rec, action, True)
    advance()


def bot_action(key):
    rec = get_strategy(st.session_state.bot_card, key)
    action = "p" if random.random() < rec[0] else "b"

    if action == "p":
        label = "L'IA checke." if key == "p" else "L'IA se couche."
    else:
        label = "L'IA mise." if key == "p" else "L'IA suit."

    st.session_state.feed.append(label)
    st.session_state.history += action
    st.session_state.last_recommendation = (rec, action, False)
    advance()


def advance():
    h = st.session_state.history
    if h == "p":
        bot_action("p")
        return
    if h == "b":
        bot_action("b")
        return
    if h == "pb":
        st.session_state.stage = "human_facing"
        return
    resolve_hand(h)


def resolve_hand(h):
    human_higher = st.session_state.human_card > st.session_state.bot_card

    if h == "pp":
        net = 1 if human_higher else -1
        outcome = "Showdown, vous gagnez." if human_higher else "Showdown, l'IA gagne."
    elif h == "bp":
        net = 1
        outcome = "L'IA se couche, vous remportez la mise."
    elif h == "bb":
        net = 2 if human_higher else -2
        outcome = "Showdown après double mise, vous gagnez." if human_higher else "Showdown après double mise, l'IA gagne."
    elif h == "pbp":
        net = -1
        outcome = "Vous vous couchez, l'IA remporte la mise."
    else:  # pbb
        net = 2 if human_higher else -2
        outcome = "Showdown après relance suivie, vous gagnez." if human_higher else "Showdown après relance suivie, l'IA gagne."

    st.session_state.human_chips += net
    st.session_state.bot_chips -= net
    st.session_state.hands_played += 1
    st.session_state.feed.append(
        f"{outcome} (Vous aviez {CARD_NAMES[st.session_state.human_card]}, "
        f"l'IA avait {CARD_NAMES[st.session_state.bot_card]})"
    )
    st.session_state.stage = "hand_over"


init_state()

st.title("Kuhn Poker contre une IA entraînée par CFR")
st.caption(
    "L'IA a appris sa stratégie par Counterfactual Regret Minimization (CFR), "
    "l'algorithme derrière les meilleurs bots de poker. Chaque décision est "
    "comparée à la stratégie théoriquement optimale (GTO)."
)

col1, col2 = st.columns(2)
col1.metric("Vos jetons", st.session_state.human_chips)
col2.metric("Jetons IA", st.session_state.bot_chips)

col1, col2 = st.columns(2)
with col1:
    st.subheader("Vous")
    st.info(CARD_NAMES[st.session_state.human_card])
with col2:
    st.subheader("IA")
    if st.session_state.stage == "hand_over":
        st.info(CARD_NAMES[st.session_state.bot_card])
    else:
        st.info("Cachée")

for line in st.session_state.feed:
    st.write(line)

if st.session_state.last_recommendation is not None:
    rec, action, is_human = st.session_state.last_recommendation
    check_pct = round(rec[0] * 100)
    bet_pct = 100 - check_pct
    recommended_label = "miser/suivre" if rec[1] > rec[0] else "checker/se coucher"
    chosen_label = "miser/suivre" if action == "b" else "checker/se coucher"
    who = "Votre choix" if is_human else "Choix de l'IA"
    match = "correspond à" if recommended_label == chosen_label else "diffère de"

    st.progress(bet_pct / 100)
    st.caption(
        f"Recommandation GTO : {check_pct}% check/fold, {bet_pct}% bet/call. "
        f"{who} ({chosen_label}) {match} la recommandation dominante."
    )

if st.session_state.stage == "human_turn":
    c1, c2 = st.columns(2)
    if c1.button("Checker", use_container_width=True):
        human_action("p", "root")
        st.rerun()
    if c2.button("Miser", use_container_width=True):
        human_action("b", "root")
        st.rerun()
elif st.session_state.stage == "human_facing":
    c1, c2 = st.columns(2)
    if c1.button("Se coucher", use_container_width=True):
        human_action("p", "pb")
        st.rerun()
    if c2.button("Suivre", use_container_width=True):
        human_action("b", "pb")
        st.rerun()
elif st.session_state.stage == "hand_over":
    if st.button("Nouvelle main", use_container_width=True):
        deal_new_hand()
        st.rerun()

st.divider()
total = st.session_state.gto_total
pct = round(100 * st.session_state.gto_aligned / total) if total else 0
st.caption(f"Mains jouées : {st.session_state.hands_played}  -  Décisions alignées avec le GTO : {pct} %")
