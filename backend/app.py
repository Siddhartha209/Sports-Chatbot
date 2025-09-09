from flask import Flask, request, jsonify
from flask_cors import CORS
import spacy
import json
import os
import random
import re
from typing import List, Dict, Tuple, Optional
from fuzzywuzzy import process, fuzz

app = Flask(__name__)
CORS(app)

# ---------------------------
# Load NLP
# ---------------------------
nlp = spacy.load("en_core_web_sm", disable=["textcat"])
# We’ll still use tokenizer, tagger, parser, ner (from sm model)

# ---------------------------
# Load data
# ---------------------------
JSON_PATH = os.path.join(os.path.dirname(__file__), "..", "sports-chatbot", "public", "player_stats.json")
with open(JSON_PATH, "r", encoding="utf-8") as f:
    data_list = json.load(f)
    # Normalize keys to strings, keep original dict per player
    players_data: Dict[str, Dict] = {p["player"]: p for p in data_list}

ALL_PLAYER_NAMES = list(players_data.keys())

# ---------------------------
# Stat keywords / synonyms
# ---------------------------
# Expandable: add any phrasing you expect from users. Keys are *phrases* you might see.
STAT_SYNONYMS = {
    # Basic info
    "team": "team", "club": "team",
    "player": "player", "name": "player",
    "position": "position", "role": "position",
    "age": "age", "born": "born", "dob": "born",
    "nation": "nation", "nationality": "nation",
    "country": "nation", "plays for": "nation", "represents": "nation",
    "represents country": "nation", "national team": "nation",
    "which country": "nation", "his nation": "nation",

    # Appearances & minutes
    "appearance": "matches_played", "appearances": "matches_played", "games": "matches_played",
    "matches": "matches_played", "apps": "matches_played",
    "starts": "starts",
    "minutes": "minutes_played", "minutes played": "minutes_played",
    "full matches": "full_matches_played",

    # Goals & assists
    "goal": "goals", "goals": "goals", "scored": "goals", "scores": "goals",
    "non penalty goals": "non_penalty_goals",
    "goals per 90": "goals_per_90", "g/90": "goals_per_90",
    "assist": "assists", "assists": "assists",
    "assists per 90": "assists_per_90", "a/90": "assists_per_90",
    "g+a": "goal_involvements", "goal contributions": "goal_involvements",
    "non penalty g+a": "non_penalty_goal_involvements",

    # Expected goals & assists
    "expected goal": "expected_goals", "expected goals": "expected_goals", "xg": "expected_goals",
    "npxg": "non_penalty_expected_goals",
    "npxg/shot": "non_penalty_expected_goals_per_shot",
    "expected assist": "expected_assists", "expected assists": "expected_assists", "xa": "expected_assists",
    "xag": "expected_assists",
    "xg+xag": "expected_goal_involvements",
    "npxg+xag": "non_penalty_expected_goal_involvements",
    "goals minus xg": "goals_minus_expected",
    "non penalty goals minus xg": "non_penalty_goals_minus_expected",

    # Shooting
    "shot": "shots", "shots": "shots",
    "shots per 90": "shots_per_90",
    "on target": "shots_on_target", "shots on target": "shots_on_target",
    "shots on target per 90": "shots_on_target_per_90",
    "shot accuracy": "shots_on_target_pct", "accuracy": "shots_on_target_pct",
    "goals per shot": "goals_per_shot",
    "goals per shot on target": "goals_per_shot_on_target",
    "distance": "average_shot_distance", "avg shot distance": "average_shot_distance",
    "free kick": "free_kicks", "free kicks": "free_kicks",
    "penalty": "penalties_scored", "penalties": "penalties_scored", "pens": "penalties_scored",
    "penalty attempts": "penalty_attempts",

    # Passing & carrying
    "progressive carries": "progressive_carries", "prog carries": "progressive_carries",
    "progressive passes": "progressive_passes", "prog passes": "progressive_passes",
    "progressive runs": "progressive_receives", "prog runs": "progressive_receives",
    "cross": "crosses", "crosses": "crosses",

    # Defensive
    "tackle": "tackles_won", "tackles": "tackles_won",
    "interception": "interceptions", "interceptions": "interceptions",
    "recovery": "recoveries", "recoveries": "recoveries",
    "duels won": "duels_won", "duels lost": "duels_lost",
    "duel win%": "duel_win_pct", "win%": "duel_win_pct",

    # Discipline
    "foul": "fouls_committed", "fouls": "fouls_committed",
    "fouled": "fouled",
    "offside": "offsides", "offsides": "offsides",
    "yellow card": "yellow_cards", "yellow cards": "yellow_cards",
    "second yellow": "second_yellow_cards", "second yellow cards": "second_yellow_cards",
    "red card": "red_cards", "red cards": "red_cards",
    "own goal": "own_goals", "own goals": "own_goals",

    # Penalties (won/conceded/saved)
    "penalty won": "penalties_won", "penalties won": "penalties_won",
    "penalty conceded": "penalties_conceded", "penalties conceded": "penalties_conceded",
    "penalties against": "penalties_against",
    "penalties faced": "penalties_faced",
    "penalties saved": "penalties_saved",
    "penalties missed": "penalties_missed",

    # Keeper stats
    "saves": "saves",
    "shots on target against": "shots_on_target_against",
    "goals against": "goals_against", "conceded": "goals_against",
    "goals against per 90": "goals_against_per_90", "ga/90": "goals_against_per_90",
    "save%": "keepers_Save%", "keepers save%": "keepers_Save%",
    "clean sheet": "clean_sheets", "clean sheets": "clean_sheets",
    "clean sheet%": "clean_sheet_pct",

    # Match results
    "wins": "wins", "win": "wins",
    "draws": "draws", "draw": "draws",
    "losses": "losses", "loss": "losses",
}


CANON_TO_PHRASES = {}
for k, v in STAT_SYNONYMS.items():
    CANON_TO_PHRASES.setdefault(v, set()).add(k)

CANON_STATS = list(CANON_TO_PHRASES.keys())

# Superlative markers
SUPERLATIVE_MARKERS = {"most", "highest", "best", "top", "leading", "leader", "highest number", "max"}

# ---------------------------
# Fuzzy helpers
# ---------------------------
def fuzzy_find_players(text: str, limit: int = 5, threshold: int = 80) -> List[str]:
    """Return likely player names referenced anywhere in text (handles short & long queries)."""
    matches = process.extract(text, ALL_PLAYER_NAMES, limit=limit, scorer=fuzz.token_set_ratio)
    return [name for name, score in matches if score >= threshold]

def fuzzy_match_stat_phrases(text: str, threshold: int = 85) -> List[str]:
    """Return canonical stat keys mentioned in text (robust to phrasing)."""
    found = set()
    for phrase, canon in STAT_SYNONYMS.items():
        # Check both fuzzy and literal containment to catch short phrases like "xg"
        score = fuzz.partial_ratio(text, phrase)
        if phrase in text or score >= threshold:
            found.add(canon)
    return list(found)

# ---------------------------
# NLP extraction
# ---------------------------
def extract_players(doc) -> List[str]:
    # 1) Use NER PERSON + PROPN sequences as candidate names
    candidates = set()
    # From entities
    for ent in doc.ents:
        if ent.label_ in ("PERSON", "ORG"):  # sometimes clubs/players get mixed
            candidates.add(ent.text)
    # From proper noun chunks
    chunk = []
    for token in doc:
        if token.pos_ == "PROPN":
            chunk.append(token.text)
        else:
            if chunk:
                candidates.add(" ".join(chunk))
                chunk = []
    if chunk:
        candidates.add(" ".join(chunk))

    # 2) Fuzzy match any candidate against known players
    matched = set()
    # Also try the full text (helps for short queries like "saka goals")
    for cand in list(candidates) + [doc.text]:
        for p in fuzzy_find_players(cand):
            matched.add(p)

    return list(matched)

def extract_stats(doc) -> List[str]:
    text = doc.text.lower()
    return fuzzy_match_stat_phrases(text)

def extract_superlative(doc) -> bool:
    text = doc.text.lower()
    return any(marker in text for marker in SUPERLATIVE_MARKERS)

def extract_team_constraint(doc) -> Optional[str]:
    """
    Try to capture a team constraint like 'for Arsenal' or 'in Man City'.
    We look for prepositional phrases headed by 'for'/'in'/'at' followed by PROPNs.
    """
    text = doc.text.lower()
    # Quick patterns first
    m = re.search(r"\b(for|in|at)\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)", doc.text)
    if m:
        return m.group(2)
    # Fallback: look for ORG entities not equal to players
    orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
    if orgs:
        # Return the first org that isn't a player name
        for org in orgs:
            if org not in players_data:
                return org
    return None

# ---------------------------
# Intents
# ---------------------------
class Intent:
    GET_PLAYER_STATS = "GET_PLAYER_STATS"         # e.g., "how many goals has saka scored?"
    COMPARE_PLAYERS = "COMPARE_PLAYERS"           # e.g., "who has more assists, saka or martinelli?"
    LEADERBOARD = "LEADERBOARD"                   # e.g., "which player has the most goals?"
    HELP = "HELP"                                 # e.g., "what can I ask?" / "list stats"
    UNKNOWN = "UNKNOWN"

def detect_intent(players: List[str], stats: List[str], is_superlative: bool) -> str:
    if is_superlative and stats:
        return Intent.LEADERBOARD
    if len(players) >= 2 and stats:
        return Intent.COMPARE_PLAYERS
    if players and (stats or True):  # even if no stat, we can ask follow-up or show quick summary
        return Intent.GET_PLAYER_STATS
    return Intent.UNKNOWN

# ---------------------------
# Query layer
# ---------------------------
def query_player_stats(players: List[str], stats: List[str], all_stats: bool) -> List[Tuple[str, Dict[str, str]]]:
    """
    Returns list of (player_name, dict_of_stat->value).
    If all_stats=True, dump everything for each player.
    """
    results = []
    for p in players:
        pdata = players_data.get(p, {})
        if not pdata:
            continue
        if all_stats:
            # Include everything; ensure stringified for JSON safety
            picked = {k: pdata.get(k, "—") for k in pdata.keys()}
        else:
            wanted = stats if stats else []  # could be empty; handled in response
            picked = {s: pdata.get(s, "—") for s in wanted}
        results.append((p, picked))
    return results

def query_leaderboard(stat: str, team: Optional[str] = None) -> Optional[Tuple[str, float]]:
    """
    Returns (player_name, best_value) for a numeric stat.
    If team is provided, filter to that team when possible.
    """
    best_name, best_val = None, None

    for name, pdata in players_data.items():
        if team:
            team_name = str(pdata.get("team", "")).lower()
            if fuzz.partial_ratio(team_name, team.lower()) < 85:
                continue

        val = pdata.get(stat, None)
        # Try to coerce to float if it's numeric-like; otherwise skip
        try:
            if isinstance(val, str):
                val = val.replace(",", "").replace("%", "").strip()
            val_num = float(val)
        except Exception:
            continue

        if best_val is None or val_num > best_val:
            best_val = val_num
            best_name = name

    if best_name is None:
        return None
    return (best_name, best_val)

# ---------------------------
# Response generation
# ---------------------------
ACKS = [
    "Got it.",
    "Sure thing.",
    "Alright.",
    "Absolutely.",
    "On it."
]

def natural_join(items: List[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + f" and {items[-1]}"

def render_player_stat_line(player: str, picked: Dict[str, str]) -> str:
    if not picked:
        return f"I didn’t catch which stat you want for {player}."
    bits = []
    for stat, val in picked.items():
        pretty = stat.replace("_", " ")
        bits.append(f"{pretty}: {val}")
    return f"{player} — " + "; ".join(bits)

def friendly_stat_sentence(player: str, picked: Dict[str, str]) -> str:
    # Conversational summary for a single player
    if not picked:
        return f"What would you like to know about {player}?"
    templates = [
        f"{player} currently has " + ", ".join([f"{s.replace('_', ' ')}: {v}" for s, v in picked.items()]) + ".",
        f"So far, {player} has recorded " + ", ".join([f"{s.replace('_', ' ')}: {v}" for s, v in picked.items()]) + ".",
        f"In this season, {player} has " + ", ".join([f"{s.replace('_', ' ')}: {v}" for s, v in picked.items()]) + ".",
    ]
    return random.choice(templates)

def render_full_block(player: str, pdata: Dict[str, str]) -> str:
    # Pretty full dump for that player
    key_lines = []
    for k, v in pdata.items():
        pretty = k.replace("_", " ")
        key_lines.append(f"- {pretty}: {v}")
    return f"📊 Full stats for {player}:\n" + "\n".join(key_lines)

def response_help() -> str:
    examples = [
        "How many goals has Bukayo Saka scored?",
        "Goals scored by Saka",
        "Which player has the most assists?",
        "Who has more xG — Haaland or Salah?",
        "Show me all stats for Son",
        "Top player for progressive carries at Arsenal",
    ]
    return (
        "You can ask me about players, stats, comparisons, and leaders. "
        "Try things like:\n• " + "\n• ".join(examples)
    )

# ---------------------------
# Chat endpoint
# ---------------------------
@app.route("/chat", methods=["POST"])
def chat():
    payload = request.json or {}
    user_input = (payload.get("query") or "").strip()
    if not user_input:
        return jsonify({"response": "Tell me what you’d like to know — a player, a stat, a comparison… I’ve got you. 😊"})

    doc = nlp(user_input)

    # Quick “all stats” detector
    text_lower = user_input.lower()
    all_stats_requested = any(phrase in text_lower for phrase in ["all stats", "everything", "full stats", "every stat", "show all"])

    # Extract entities/intents
    matched_players = extract_players(doc)
    requested_stats = extract_stats(doc)
    is_superlative = extract_superlative(doc)
    team_constraint = extract_team_constraint(doc)

    # If user explicitly asked for "help" / "what can I ask"
    if re.search(r"\b(help|how to|what can i ask|examples|commands)\b", text_lower):
        return jsonify({"response": response_help()})

    intent = detect_intent(matched_players, requested_stats, is_superlative)

    # ---------------------------
    # Intent routing
    # ---------------------------
    if intent == Intent.LEADERBOARD:
        if not requested_stats:
            return jsonify({"response": "Which stat would you like the leader for? (e.g., goals, assists, xG)"})
        # If multiple stats, answer for the first one mentioned (or iterate)
        answers = []
        for stat in requested_stats:
            result = query_leaderboard(stat, team_constraint)
            if result is None:
                pretty = stat.replace("_", " ")
                if team_constraint:
                    answers.append(f"I couldn’t find a clear leader for {pretty} at {team_constraint}.")
                else:
                    answers.append(f"I couldn’t find a clear leader for {pretty}.")
                continue
            name, val = result
            pretty = stat.replace("_", " ")
            if team_constraint:
                answers.append(f"{random.choice(ACKS)} The {pretty} leader for {team_constraint} is {name} with {val}.")
            else:
                answers.append(f"{random.choice(ACKS)} The {pretty} leader is {name} with {val}.")
        return jsonify({"response": "\n".join(answers)})

    if intent == Intent.COMPARE_PLAYERS:
        if not requested_stats:
            return jsonify({"response": "Which stat should I compare? (e.g., goals, assists, xG)"})
        # Compare on first requested stat (or all)
        lines = []
        for stat in requested_stats:
            # Build a sorted table for the stat
            rows = []
            for p in matched_players:
                val = players_data.get(p, {}).get(stat, "—")
                try:
                    v = float(str(val).replace(",", "").replace("%", "").strip())
                except Exception:
                    v = None
                rows.append((p, v, val))
            rows.sort(key=lambda r: (r[1] is None, -(r[1] or -1e18)))
            pretty = stat.replace("_", " ")
            # Format
            ranking = " > ".join([f"{p} ({display})" for p, _, display in rows if display != "—"])
            if ranking:
                lines.append(f"For {pretty}: {ranking}.")
            else:
                lines.append(f"I couldn’t compare {pretty} for those players.")
        opener = random.choice([
            "Here’s how they stack up:",
            "Let’s line them up:",
            "Side-by-side, this is what we’ve got:"
        ])
        return jsonify({"response": opener + "\n" + "\n".join(lines)})

    if intent == Intent.GET_PLAYER_STATS:
        if not matched_players and requested_stats:
            # If stat is found but no player explicitly mentioned,
            # check if the last conversation had a player (context).
            last_player = payload.get("context", {}).get("last_player")
            if last_player:
                matched_players = [last_player]

        if matched_players and requested_stats:
            q = query_player_stats(matched_players, requested_stats, all_stats=False)
            responses = []
            for player, picked in q:
                responses.append(friendly_stat_sentence(player, picked))
            # Store last player in context for follow-ups
            return jsonify({
                "response": "\n".join(responses),
                "context": {"last_player": matched_players[-1]}
            })


        # If they asked something like "goals scored by saka" we already have stat+player
        # If they asked "saka" alone, follow up nicely.
        if not requested_stats and not all_stats_requested:
            # Provide a gentle prompt + a tiny teaser (top 3 common stats if available)
            p = matched_players[0]
            pdata = players_data.get(p, {})
            teasers = []
            for key in ["goals", "assists", "matches_played"]:
                if key in pdata:
                    teasers.append(f"{key.replace('_', ' ')}: {pdata[key]}")
            if teasers:
                return jsonify({"response": f"What would you like to know about {p}? For example — {', '.join(teasers)}."})
            return jsonify({"response": f"What would you like to know about {p}? (goals, assists, xG, minutes…)"})

        results = []
        # If all stats: dump everything per player
        if all_stats_requested:
            for p in matched_players:
                pdata = players_data.get(p, {})
                if not pdata:
                    continue
                results.append(render_full_block(p, pdata))
            return jsonify({"response": "\n\n".join(results)})

        # Else: pick the requested stats and speak naturally
        q = query_player_stats(matched_players, requested_stats, all_stats=False)
        for player, picked in q:
            results.append(friendly_stat_sentence(player, picked))
        return jsonify({"response": "\n".join(results)})

    if intent == Intent.UNKNOWN:
        # Try to at least identify a player or a stat and guide the user
        maybe_players = extract_players(doc)
        maybe_stats = extract_stats(doc)
        if maybe_players and not maybe_stats:
            return jsonify({"response": f"What would you like to know about {natural_join(maybe_players)}? (e.g., goals, assists, xG)"} )
        if maybe_stats and not maybe_players:
            pretty = natural_join([s.replace("_", " ") for s in maybe_stats])
            return jsonify({"response": f"Got it — {pretty}. Which player should I look up?"})
        return jsonify({"response": "I didn’t quite catch that. You can ask things like: 'How many goals has Saka scored?' or 'Which player has the most assists?'"})

    # Fallback (shouldn’t reach)
    return jsonify({"response": "Something went odd on my side — mind rephrasing that? 🙏"})


if __name__ == "__main__":
    app.run(port=5000, debug=True)
