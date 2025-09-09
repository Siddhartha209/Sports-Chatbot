import requests
from bs4 import BeautifulSoup, Comment
import json
import time
from typing import List, Dict, Any
import pandas as pd
import unicodedata

class FBRefScraper:
    def __init__(self, delay: float = 1.0):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def get_page(self, url: str) -> BeautifulSoup:
        try:
            response = self.session.get(url)
            response.raise_for_status()
            time.sleep(self.delay)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Parse tables inside HTML comments
            comments = soup.find_all(string=lambda text: isinstance(text, Comment))
            for c in comments:
                if '<table' in c:
                    comment_soup = BeautifulSoup(c, 'html.parser')
                    soup.append(comment_soup)
            return soup
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch {url}: {str(e)}")

    def clean_value(self, value: str) -> Any:
        if not value or value.strip() == '':
            return None
        value = value.strip()
        try:
            if value.endswith('%'):
                return float(value[:-1])
            elif value.isdigit():
                return int(value)
            else:
                return float(value)
        except ValueError:
            return value

    def remove_accents(self, text: str) -> str:
        if not text:
            return text
        # Normalize to NFKD form, then keep only ASCII characters
        return ''.join(c for c in unicodedata.normalize('NFKD', text) if ord(c) < 128)

    def extract_table(self, url: str) -> List[Dict[str, Any]]:
        soup = self.get_page(url)
        tables = soup.find_all('table')
        if not tables:
            raise Exception("No tables found on the page")

        # Pick largest table
        table = max(tables, key=lambda t: len(t.find_all('tr')))
        thead = table.find('thead')
        header_rows = thead.find_all('tr')
        headers = [th.get_text(strip=True) for th in header_rows[-1].find_all(['th', 'td'])]

        tbody = table.find('tbody')
        data = []
        for row in tbody.find_all('tr'):
            if row.get('class') and 'thead' in row.get('class', []):
                continue
            cells = row.find_all(['td', 'th'])
            if len(cells) != len(headers):
                continue
            row_data = {}
            team = None
            player = None
            for i, cell in enumerate(cells):
                header = headers[i]
                text = cell.get_text(strip=True)
                if header == 'Player':
                    player = text
                    link = cell.find('a')
                    if link:
                        row_data['Player_URL'] = link.get('href', '')
                elif header == 'Squad':
                    team = text
                    link = cell.find('a')
                    if link:
                        row_data['Squad_URL'] = link.get('href', '')
                row_data[header] = self.clean_value(text)
            if team and player:
                data.append({'team': team, 'player': player, 'stats': row_data})
        return data

    def scrape_and_flatten(self, urls: Dict[str, str], save_file: str = 'player_stats.json') -> pd.DataFrame:
        flattened_data: list[dict] = []
        player_index: dict[str, dict] = {}  # key = team + player to avoid duplicates

        # --- 1️⃣ Scrape data ---
        for category, url in urls.items():
            print(f"\nScraping {category} stats from: {url}")
            try:
                data = self.extract_table(url)
                for item in data:
                    team = item['team']
                    player = item['player']
                    stats = item['stats']

                    key = f"{team}_{player}"
                    if key not in player_index:
                        player_index[key] = {'Team': team, 'Player': player}

                    for k, v in stats.items():
                        if k not in ['Player', 'Squad']:
                            player_index[key][f"{category}_{k}"] = v
            except Exception as e:
                print(f"Error scraping {category}: {e}")

        flattened_data = list(player_index.values())

        # --- 2️⃣ Remove unwanted columns ---
        columns_to_remove = [
            "shooting_Player_URL", "shooting_Squad_URL", "shooting_Matches", "shooting_Rk",
            "misc_Rk", "misc_Player_URL", "misc_Nation", "misc_Pos", "misc_Squad_URL", "misc_Age",
            "misc_Born", "misc_90s", "misc_Matches",
            "standard_stats_Rk", "standard_stats_Player_URL", "standard_stats_Nation", "standard_stats_Pos",
            "standard_stats_Squad_URL", "standard_stats_Age", "standard_stats_Born", "standard_stats_Matches",
            "keepers_Rk", "keepers_Player_URL", "keepers_Nation", "keepers_Pos", "keepers_Squad_URL",
            "keepers_Age", "keepers_Born", "keepers_MP", "keepers_Starts", "keepers_Min", "keepers_90s",
            "keepers_Matches", "standard_stats_90s", "standard_stats_PK", "standard_stats_PKatt",
            "standard_stats_CrdY", "standard_stats_CrdR", "standard_stats_xG", "standard_stats_npxG"
        ]
        for player_dict in flattened_data:
            for col in columns_to_remove:
                player_dict.pop(col, None)

        # --- 3️⃣ Compute total assists as integer ---
        for player_dict in flattened_data:
            try:
                per90_assists = player_dict.get("standard_stats_Ast", 0.0) or 0.0
                ninety_minutes = player_dict.get("shooting_90s", 0) or 0
                player_dict["Assists"] = int(round(per90_assists * ninety_minutes))

            except Exception as e:
                player_dict["Assists"] = 0
                print(f"Error computing Assists for {player_dict.get('player')}: {e}")

        # --- 4️⃣ Rename keys ---
        rename_map = {
            "Player": "player",
            "Team": "team",
            "shooting_Pos": "position",
            "shooting_Age": "age",
            "shooting_Born": "born",
            "shooting_Nation": "nation",
            "standard_stats_MP": "matches_played",
            "standard_stats_Starts": "starts",
            "standard_stats_Min": "minutes_played",
            "shooting_90s": "full_matches_played",
            "shooting_Gls": "goals",
            "standard_stats_Gls": "goals_per_90",
            "standard_stats_G-PK": "non_penalty_goals",
            "Assists": "assists",
            "standard_stats_Ast": "assists_per_90",
            "standard_stats_G+A": "goal_involvements",
            "standard_stats_G+A-PK": "non_penalty_goal_involvements",
            "shooting_G-xG": "goals_minus_expected",
            "shooting_np:G-xG": "non_penalty_goals_minus_expected",
            "standard_stats_xAG": "expected_assists",
            "standard_stats_xG+xAG": "expected_goal_involvements",
            "standard_stats_npxG+xAG": "non_penalty_expected_goal_involvements",
            "shooting_Sh": "shots",
            "shooting_Sh/90": "shots_per_90",
            "shooting_SoT": "shots_on_target",
            "shooting_SoT/90": "shots_on_target_per_90",
            "shooting_SoT%": "shots_on_target_pct",
            "shooting_G/Sh": "goals_per_shot",
            "shooting_G/SoT": "goals_per_shot_on_target",
            "shooting_Dist": "average_shot_distance",
            "shooting_FK": "free_kicks",
            "shooting_PK": "penalties_scored",
            "shooting_PKatt": "penalty_attempts",
            "shooting_xG": "expected_goals",
            "shooting_npxG": "non_penalty_expected_goals",
            "shooting_npxG/Sh": "non_penalty_expected_goals_per_shot",
            "misc_TklW": "tackles_won",
            "misc_Int": "interceptions",
            "misc_Recov": "recoveries",
            "misc_Won": "duels_won",
            "misc_Lost": "duels_lost",
            "misc_Won%": "duel_win_pct",
            "misc_Fls": "fouls_committed",
            "misc_Fld": "fouled",
            "misc_Off": "offsides",
            "misc_Crs": "crosses",
            "misc_CrdY": "yellow_cards",
            "misc_2CrdY": "second_yellow_cards",
            "misc_CrdR": "red_cards",
            "misc_OG": "own_goals",
            "misc_PKwon": "penalties_won",
            "misc_PKcon": "penalties_conceded",
            "standard_stats_PrgC": "progressive_carries",
            "standard_stats_PrgP": "progressive_passes",
            "standard_stats_PrgR": "progressive_receives",
            "keepers_Saves": "saves",
            "keepers_SoTA": "shots_on_target_against",
            "keepers_GA": "goals_against",
            "keepers_GA90": "goals_against_per_90",
            "keepers_CS": "clean_sheets",
            "keepers_CS%": "clean_sheet_pct",
            "keepers_PKA": "penalties_against",
            "keepers_PKatt": "penalties_faced",
            "keepers_PKsv": "penalties_saved",
            "keepers_PKm": "penalties_missed",
            "keepers_W": "wins",
            "keepers_D": "draws",
            "keepers_L": "losses",
        }
        for player_dict in flattened_data:
            for old_key, new_key in rename_map.items():
                if old_key in player_dict:
                    player_dict[new_key] = player_dict.pop(old_key)

        # --- 5️⃣ Normalize nation ---
        three_letter_codes = {
            "engENG": "England",
            "wlsWAL": "Wales",
            "sctSCO": "Scotland",
            "nirNIR": "Northern Ireland"
        }
        nation_map = {
            "en": "England", "nl": "Netherlands", "fr": "France", "br": "Brazil", "es": "Spain",
            "pt": "Portugal", "de": "Germany", "dk": "Denmark", "ar": "Argentina", "wls": "Wales",
            "it": "Italy", "be": "Belgium", "sct": "Scotland", "se": "Sweden", "ie": "Republic of Ireland",
            "no": "Norway", "ci": "Côte d'Ivoire", "sn": "Senegal", "ng": "Nigeria", "ch": "Switzerland",
            "us": "United States", "nir": "Northern Ireland", "cm": "Cameroon", "jp": "Japan", "co": "Colombia",
            "ma": "Morocco", "rs": "Serbia", "cd": "Congo DR", "uy": "Uruguay", "cz": "Czech Republic",
            "mx": "Mexico", "gh": "Ghana", "hu": "Hungary", "eg": "Egypt", "ua": "Ukraine", "py": "Paraguay",
            "tr": "Türkiye", "pl": "Poland", "kr": "Korea Republic", "si": "Slovenia", "at": "Austria",
            "hr": "Croatia", "ec": "Ecuador", "mz": "Mozambique", "sk": "Slovakia", "zw": "Zimbabwe",
            "za": "South Africa", "gm": "Gambia", "nz": "New Zealand", "tn": "Tunisia", "dz": "Algeria",
            "bg": "Bulgaria", "gw": "Guinea-Bissau", "bf": "Burkina Faso", "ht": "Haiti", "pe": "Peru",
            "uz": "Uzbekistan", "gr": "Greece", "ge": "Georgia", "is": "Iceland", "il": "Israel",
            "jm": "Jamaica", "tt": "Trinidad and Tobago"
        }

        for player_dict in flattened_data:
            raw_nation = player_dict.get("nation", "")
            if raw_nation in three_letter_codes:
                player_dict["nation"] = three_letter_codes[raw_nation]
            elif raw_nation:
                code = raw_nation[:2].lower()
                player_dict["nation"] = nation_map.get(code, raw_nation)
            else:
                player_dict["nation"] = None

        for player_dict in flattened_data:
            player_dict['player'] = self.remove_accents(player_dict.get('player', ''))


        # --- 6️⃣ Save JSON ---
        with open(save_file, 'w', encoding='utf-8') as f:
            json.dump(flattened_data, f, indent=2, ensure_ascii=False)
        print(f"\nFlattened and cleaned data saved to {save_file}")

        # --- 7️⃣ Convert to DataFrame ---
        df = pd.DataFrame(flattened_data)

        return df






if __name__ == "__main__":
    scraper = FBRefScraper(delay=1.0)

    urls = {
        "shooting": "https://fbref.com/en/comps/9/shooting/Premier-League-Stats",
        "misc": "https://fbref.com/en/comps/9/misc/Premier-League-Stats",
        "standard_stats": "https://fbref.com/en/comps/9/stats/Premier-League-Stats",
        "keepers": "https://fbref.com/en/comps/9/keepers/Premier-League-Stats"
    }

    # Update the save_file path to point to your public folder
    save_path = '../chatbot-sports/backend/player_stats.json'
    df = scraper.scrape_and_flatten(urls, save_file=save_path)

    #print(f"\nDataFrame shape: {df.shape}")
    #print(df.head())

