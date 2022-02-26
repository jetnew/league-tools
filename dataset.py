# Ref: https://hextechdocs.dev/crawling-matches-using-the-riot-games-api/
# Ref: https://developer.riotgames.com/apis#match-v5
# Ref: https://riot-watcher.readthedocs.io/en/latest/riotwatcher/LeagueOfLegends/MatchApiV5.html#riotwatcher._apis.league_of_legends.MatchApiV5
# Ref: https://developer.riotgames.com/app/555087/info

from datetime import datetime
import json
import pandas as pd
from tqdm import tqdm
from riotwatcher import LolWatcher

with open("config.json") as f:
    api_key = json.load(f)["api-key"]

# Config
queue = 'RANKED_SOLO_5x5'
tier = 'PLATINUM'
divisions = ['I', 'II', 'III', 'IV']

# Init
lolw = LolWatcher(api_key)
match_ids = []
match_data = []


try:
    # Collect data
    for div in tqdm(divisions):

        # Get all players within a division
        players = lolw.league.entries('na1', queue, tier, div)

        # Get all matches of each player
        for player in tqdm(players, leave=False):
            id = player['summonerId']
            summoner = lolw.summoner.by_id('na1', id)
            matches = lolw.match.matchlist_by_puuid('americas', summoner['puuid'], count=20)

            # For each match, get the match entry
            for match_id in tqdm(matches, leave=False):

                # Skip match if already collected
                if match_id in match_ids:
                    continue
                else:
                    match_ids.append(match_id)

                match = lolw.match.by_id('americas', match_id)

                # Skip match if not classic
                game_mode = match['info']['gameMode']
                if game_mode != 'CLASSIC':
                    continue

                # Get data
                players = match['info']['participants']
                game_time = match['info']['gameStartTimestamp']
                game_duration = match['info']['gameDuration']

                # Compute stuff
                champions = [None] * 10

                for player in players:
                    champion = player['championName']
                    role = player['teamPosition']
                    idx = 0 if player['win'] else 5
                    if role == 'JUNGLE':
                        idx += 1
                    elif role == 'MIDDLE':
                        idx += 2
                    elif role == 'BOTTOM':
                        idx += 3
                    elif role == 'UTILITY':
                        idx += 4
                    champions[idx] = champion

                # Collect data
                data = {
                    "match_id": match_id,
                    "game_time": game_time,
                    "game_duration": game_duration,
                    **{
                        f"player{i}": champions[i] for i in range(10)
                    }
                }

                match_data.append(data)
                # break
            # break
        # break
except Exception as e:
    print(f"Error: {e}")

df_matches = pd.DataFrame(match_data)
df_matches.to_csv("matches.csv")