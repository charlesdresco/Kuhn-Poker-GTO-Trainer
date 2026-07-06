import json
import random

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Kuhn Poker - IA entraînée par CFR", page_icon=":spades:", layout="centered")

STRATEGY = {
  "1": {
    "root": [0.8028800630713723, 0.19711993692862764],
    "p": [0.6627232947905609, 0.3372767052094392],
    "b": [0.9999774147406459, 0.0000225852593540616],
    "pb": [0.9999953580254475, 0.0000046419745525646]
  },
  "2": {
    "root": [0.9997425501379253, 0.0002574498620746811],
    "p": [0.9999147299871060, 0.0000852700128940598],
    "b": [0.6602374614836289, 0.3397625385163711],
    "pb": [0.4676147094753758, 0.5323852905246242]
  },
  "3": {
    "root": [0.3997072855024736, 0.6002927144975264],
    "p": [0.0000074803267407, 0.9999925196732593],
    "b": [0.0000074803267407, 0.9999925196732593],
    "pb": [0.0000094184089468, 0.9999905815910531]
  }
}

CARD_NAMES = {1: "Valet", 2: "Dame", 3: "Roi"}

CARD_VISUALS = {
    1: {"letter": "V", "suit": "\u2660", "color": "#34495e"},
    2: {"letter": "D", "suit": "\u2666", "color": "#c0392b"},
    3: {"letter": "R", "suit": "\u2665", "color": "#8e44ad"},
}

EXPLANATIONS = {
    (1, "root"): "Avec le Valet, la pire carte, on check la plupart du temps. Miser quand meme environ une fois sur cinq est un bluff volontaire : ca oblige l'adversaire a se poser des questions, et vous rend imprevisible sur la duree.",
    (1, "pb"): "Avec le Valet, si l'adversaire mise apres votre check, il faut se coucher presque a chaque fois. Le Valet ne peut jamais gagner a showdown, continuer couterait des jetons pour rien.",
    (1, "p"): "Avec le Valet, apres un check adverse, l'IA bluffe environ un tiers du temps. Cette frequence precise empeche l'adversaire de systematiquement se coucher face a un bluff.",
    (1, "b"): "Avec le Valet face a une mise directe, il faut se coucher quasiment a 100%. Payer serait perdre encore plus de jetons sur une main qui ne peut pas gagner.",
    (2, "root"): "Avec la Dame, la carte du milieu, on check presque systematiquement en premier. Trop faible pour value bet, pas assez pour bluffer utilement ici.",
    (2, "pb"): "Avec la Dame, si l'adversaire mise apres votre check, c'est le moment le plus delicat du jeu. Il faut suivre un peu plus d'une fois sur deux, juste assez pour ne pas etre exploite par les bluffs, sans sur-suivre non plus.",
    (2, "p"): "Avec la Dame, apres un check adverse, l'IA ne mise presque jamais. Trop faible pour value bet, pas assez pour un bon bluff.",
    (2, "b"): "Avec la Dame face a une mise, l'IA suit un peu plus d'un tiers du temps. C'est la frequence exacte qui l'empeche d'etre exploitee si l'adversaire bluffe trop.",
    (3, "root"): "Avec le Roi, la meilleure carte, on mise environ 60% du temps. Le reste du temps on check volontairement, pour laisser l'adversaire bluffer derriere et gagner encore plus sur la duree.",
    (3, "pb"): "Avec le Roi, si l'adversaire mise apres votre check, on suit toujours. Le Roi gagne systematiquement a showdown, il n'y a jamais de raison de se coucher.",
    (3, "p"): "Avec le Roi, apres un check adverse, l'IA mise toujours. Une main qui gagne a coup sur doit etre value bet a chaque fois pour maximiser les gains.",
    (3, "b"): "Avec le Roi face a une mise, l'IA suit toujours. C'est la meilleure carte du jeu, il n'y a jamais de raison de se coucher.",
}


def get_strategy(card, key):
    return STRATEGY[str(card)][key]


def render_card(card, hidden=False):
    if hidden:
        return (
            '<div style="width:100px;height:140px;border-radius:12px;background:#2c3e50;'
            'display:flex;align-items:center;justify-content:center;box-shadow:0 2px 6px rgba(0,0,0,0.2);">'
            '<span style="font-size:36px;color:white;">?</span></div>'
        )
    v = CARD_VISUALS[card]
    return (
        f'<div style="width:100px;height:140px;border-radius:12px;border:2px solid {v["color"]};'
        f'background:white;display:flex;flex-direction:column;align-items:center;justify-content:center;'
        f'box-shadow:0 2px 6px rgba(0,0,0,0.15);">'
        f'<div style="font-size:34px;font-weight:700;color:{v["color"]};">{v["letter"]}</div>'
        f'<div style="font-size:26px;color:{v["color"]};">{v["suit"]}</div></div>'
    )


def deal_new_hand():
    cards = [1, 2, 3]
    random.shuffle(cards)
    st.session_state.human_card = cards[0]
    st.session_state.bot_card = cards[1]
    st.session_state.history = ""
    st.session_state.feed = []
    st.session_state.stage = "human_turn"
    st.session_state.last_recommendation = None
    st.session_state.current_hand_decisions = []


def init_state():
    if "human_chips" not in st.session_state:
        st.session_state.human_chips = 0
        st.session_state.bot_chips = 0
        st.session_state.hands_played = 0
        st.session_state.gto_aligned = 0
        st.session_state.gto_total = 0
        st.session_state.card_stats = {c: {"hands": 0, "net": 0, "wins": 0} for c in [1, 2, 3]}
        st.session_state.decision_stats = {}
        st.session_state.hand_log = []
        deal_new_hand()


def record_decision(card, key, action):
    stat_key = f"{card}_{key}"
    if stat_key not in st.session_state.decision_stats:
        st.session_state.decision_stats[stat_key] = {"count": 0, "aggressive": 0}
    st.session_state.decision_stats[stat_key]["count"] += 1
    if action == "b":
        st.session_state.decision_stats[stat_key]["aggressive"] += 1


def human_action(action, key):
    rec = get_strategy(st.session_state.human_card, key)
    st.session_state.gto_total += 1
    recommended = "b" if rec[1] > rec[0] else "p"
    matched = action == recommended
    if matched:
        st.session_state.gto_aligned += 1

    record_decision(st.session_state.human_card, key, action)
    st.session_state.current_hand_decisions.append(matched)

    if action == "p":
        label = "Vous checkez." if key == "root" else "Vous vous couchez."
    else:
        label = "Vous misez." if key == "root" else "Vous suivez."

    st.session_state.feed.append(label)
    st.session_state.history += action
    st.session_state.last_recommendation = (rec, action, True, st.session_state.human_card, key)
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
    st.session_state.last_recommendation = (rec, action, False, st.session_state.bot_card, key)
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
    human_card = st.session_state.human_card
    bot_card = st.session_state.bot_card
    human_higher = human_card > bot_card

    if h == "pp":
        net = 1 if human_higher else -1
        outcome = "Showdown, vous gagnez." if human_higher else "Showdown, l'IA gagne."
    elif h == "bp":
        net = 1
        outcome = "L'IA se couche, vous remportez la mise."
    elif h == "bb":
        net = 2 if human_higher else -2
        outcome = "Showdown apres double mise, vous gagnez." if human_higher else "Showdown apres double mise, l'IA gagne."
    elif h == "pbp":
        net = -1
        outcome = "Vous vous couchez, l'IA remporte la mise."
    else:
        net = 2 if human_higher else -2
        outcome = "Showdown apres relance suivie, vous gagnez." if human_higher else "Showdown apres relance suivie, l'IA gagne."

    st.session_state.human_chips += net
    st.session_state.bot_chips -= net
    st.session_state.hands_played += 1

    stats = st.session_state.card_stats[human_card]
    stats["hands"] += 1
    stats["net"] += net
    if net > 0:
        stats["wins"] += 1

    decisions = st.session_state.current_hand_decisions
    aligned = sum(decisions)
    total = len(decisions)

    st.session_state.hand_log.append({
        "Main": st.session_state.hands_played,
        "Votre carte": CARD_NAMES[human_card],
        "Carte IA": CARD_NAMES[bot_card],
        "Sequence": h,
        "Resultat (jetons)": net,
        "Aligne GTO": f"{aligned}/{total}" if total else "-",
    })

    st.session_state.feed.append(
        f"{outcome} (Vous aviez {CARD_NAMES[human_card]}, l'IA avait {CARD_NAMES[bot_card]})"
    )
    st.session_state.stage = "hand_over"


init_state()

st.title("Kuhn Poker contre une IA entrainee par CFR")
st.caption(
    "L'IA a appris sa strategie par Counterfactual Regret Minimization (CFR), l'algorithme derriere "
    "les meilleurs bots de poker. Chaque decision est comparee a la strategie theoriquement optimale (GTO)."
)

col1, col2 = st.columns(2)
col1.metric("Vos jetons", st.session_state.human_chips)
col2.metric("Jetons IA", st.session_state.bot_chips)

col1, col2 = st.columns(2)
with col1:
    st.markdown("**Vous**")
    st.markdown(render_card(st.session_state.human_card), unsafe_allow_html=True)
with col2:
    st.markdown("**IA**")
    if st.session_state.stage == "hand_over":
        st.markdown(render_card(st.session_state.bot_card), unsafe_allow_html=True)
    else:
        st.markdown(render_card(None, hidden=True), unsafe_allow_html=True)

st.write("")
for line in st.session_state.feed:
    st.write(line)

if st.session_state.last_recommendation is not None:
    rec, action, is_human, card, key = st.session_state.last_recommendation
    check_pct = round(rec[0] * 100)
    bet_pct = 100 - check_pct
    recommended_label = "miser/suivre" if rec[1] > rec[0] else "checker/se coucher"
    chosen_label = "miser/suivre" if action == "b" else "checker/se coucher"
    who = "Votre choix" if is_human else "Choix de l'IA"
    match = "correspond a" if recommended_label == chosen_label else "differe de"

    st.progress(bet_pct / 100)
    st.caption(
        f"Recommandation GTO : {check_pct}% check/fold, {bet_pct}% bet/call. "
        f"{who} ({chosen_label}) {match} la recommandation dominante."
    )
    with st.expander("Pourquoi cette recommandation ?"):
        st.write(EXPLANATIONS.get((card, key), "Pas d'explication disponible pour cette situation."))

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
st.caption(f"Mains jouees : {st.session_state.hands_played}  -  Decisions alignees avec le GTO : {pct} %")

st.divider()
st.subheader("Vos statistiques par carte")

card_rows = []
for c in [1, 2, 3]:
    s = st.session_state.card_stats[c]
    win_rate = round(100 * s["wins"] / s["hands"]) if s["hands"] else 0
    card_rows.append({"Carte": CARD_NAMES[c], "Mains jouees": s["hands"], "Jetons nets": s["net"], "Taux de victoire (%)": win_rate})

card_df = pd.DataFrame(card_rows).set_index("Carte")
if card_df["Mains jouees"].sum() > 0:
    st.bar_chart(card_df["Jetons nets"])
    st.dataframe(card_df, use_container_width=True)
else:
    st.caption("Joue quelques mains pour voir tes statistiques apparaitre ici.")

st.subheader("Vos frequences de decision vs la theorie")
decision_rows = []
labels = {"root": "Premiere decision", "pb": "Face a une mise apres check"}
for c in [1, 2, 3]:
    for key in ["root", "pb"]:
        stat_key = f"{c}_{key}"
        if stat_key in st.session_state.decision_stats:
            d = st.session_state.decision_stats[stat_key]
            your_rate = round(100 * d["aggressive"] / d["count"])
            gto_rate = round(get_strategy(c, key)[1] * 100)
            decision_rows.append({
                "Carte": CARD_NAMES[c],
                "Situation": labels[key],
                "Nombre de fois": d["count"],
                "Votre % mise/suivi": your_rate,
                "% GTO recommande": gto_rate,
                "Ecart": your_rate - gto_rate,
            })

if decision_rows:
    st.dataframe(pd.DataFrame(decision_rows), use_container_width=True, hide_index=True)
else:
    st.caption("Joue quelques mains pour voir tes frequences de decision apparaitre ici.")

st.subheader("Historique des dernieres mains")
if st.session_state.hand_log:
    log_df = pd.DataFrame(st.session_state.hand_log[-15:][::-1])
    st.dataframe(log_df, use_container_width=True, hide_index=True)
else:
    st.caption("Aucune main terminee pour le moment.")
