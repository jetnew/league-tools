import os
import re
import pickle
import tqdm
from selenium import webdriver


def clean_name(name):
    if name == "nunu&willump":
        return "nunu"
    return name


class Champion:
    def __init__(self, name, role=None):
        self.name = name.capitalize()
        self.role = role
        self.from_cache_or_scrape()

    def from_cache_or_scrape(self):
        path = f"cache/{self.role}_{self.name}"
        if os.path.exists(path):
            with open(path + "/role_counters.pkl", 'rb') as f:
                self.role_counters = pickle.load(f)
            with open(path + "/role_counters_sorted.pkl", 'rb') as f:
                self.role_counters_sorted = pickle.load(f)
            if self.role == "Support" or self.role == "ADC":
                with open(path + "/partner_counters.pkl", 'rb') as f:
                    self.partner_counters = pickle.load(f)
                with open(path + "/partner_counters_sorted.pkl", 'rb') as f:
                    self.partner_counters_sorted = pickle.load(f)
                with open(path + "/partner_synergies.pkl", 'rb') as f:
                    self.partner_synergies = pickle.load(f)
                with open(path + "/partner_synergies_sorted.pkl", 'rb') as f:
                    self.partner_synergies_sorted = pickle.load(f)
        else:
            op = webdriver.ChromeOptions()
            op.add_argument('headless')
            driver = webdriver.Chrome(executable_path="chromedriver.exe", options=op)
            if self.role is None:
                driver.get(f"https://champion.gg/champion/{self.name}")
                r = re.compile(r'\bTop\b | \bJungle\b | \bMiddle\b | \bADC\b | \bSupport\b', flags=re.X)
                self.role = r.findall(driver.current_url)[0]
            else:
                driver.get(f"https://champion.gg/champion/{self.name}/{self.role}")
            self.driver = driver
            self.collect_winrates()
            self.cache()
            self.driver.close()

    def cache(self):
        path = f"cache/{self.role}_{self.name}"
        os.mkdir(path)
        with open(path + "/role_counters.pkl", 'wb') as f:
            pickle.dump(self.role_counters, f)
        with open(path + "/role_counters_sorted.pkl", 'wb') as f:
            pickle.dump(self.role_counters_sorted, f)
        if self.role == "Support" or self.role == "ADC":
            with open(path + "/partner_counters.pkl", 'wb') as f:
                pickle.dump(self.partner_counters, f)
            with open(path + "/partner_counters_sorted.pkl", 'wb') as f:
                pickle.dump(self.partner_counters_sorted, f)
            with open(path + "/partner_synergies.pkl", 'wb') as f:
                pickle.dump(self.partner_synergies, f)
            with open(path + "/partner_synergies_sorted.pkl", 'wb') as f:
                pickle.dump(self.partner_synergies_sorted, f)

    def collect_winrates(self):
        # Expand winrate lists
        see_more = True
        while see_more:
            elems = self.driver.find_elements_by_class_name("show-more")
            for e in elems:
                e.click()
            if len(elems) == 0:
                see_more = False

        # Get winrates
        sections = self.driver.find_elements_by_class_name("counter-column")
        for i, section in enumerate(sections):
            champs = section.find_elements_by_class_name("animate-repeat")
            counters = {}
            ranked_list = []
            for c in champs:
                name, games, winrate = c.text.split('\n')
                name = clean_name(name.lower().replace(' ', '').replace('\'', '').replace('.', '')).capitalize()
                games = int(games.split(' ')[0])
                winrate = float(winrate[:-1])

                counters[name] = (games, winrate)
                ranked_list.append((name, games, winrate))

            if i == 0:
                self.role_counters = counters
                self.role_counters_sorted = ranked_list
            elif i == 1:
                self.partner_counters = counters
                self.partner_counters_sorted = ranked_list
            elif i == 2:
                self.partner_synergies = counters
                self.partner_synergies_sorted = ranked_list[::-1]


class Matchup:
    def __init__(self, ally, enemy):
        self.ally = ally
        self.enemy = enemy
        self.collect_winrates()

    def collect_winrates(self):
        for role, champ in ally.items():
            if champ != '':
                self.ally[role] = Champion(champ, role)
        for role, champ in enemy.items():
            if champ != '':
                self.enemy[role] = Champion(champ, role)

    def print_reccs(self, reccs, title, reverse_winrate=False):
        if self.verbose:
            print(title + ':')
            for name, games, winrate in reccs:
                if reverse_winrate:
                    winrate = 100 - winrate
                print(f"{name} ({games}): {winrate}%")
            print()

    def recommend(self, role, k=5, verbose=False):
        role = role.capitalize()
        self.verbose = verbose
        if role != 'Support' and role != 'ADC':
            reccs = self.enemy[role].role_counters_sorted[:k]
            self.print_reccs(reccs, f"Champion Recommendation Against Enemy {self.enemy[role].name}", reverse_winrate=True)
            return reccs
        else:
            if role == 'Support':
                if self.enemy['ADC'] != '':
                    reccs = self.enemy['ADC'].partner_counters_sorted[:k]
                    self.print_reccs(reccs, f"Champion Recommendation Against Enemy {self.enemy['ADC'].name}", reverse_winrate=True)
                    return reccs
                if self.ally['ADC'] != '':
                    reccs = self.ally['ADC'].partner_synergies_sorted[:k]
                    self.print_reccs(reccs, f"Champion Recommendation With Ally {self.ally['ADC'].name}")
                    return reccs
                if self.enemy['Support'] != '':
                    reccs = self.enemy['support'].role_counters_sorted[:k]
                    self.print_reccs(reccs, f"Champion Recommendation Against Enemy {self.enemy['support'].name}", reverse_winrate=True)
                    return reccs

            if role == 'ADC':
                if self.ally['Support'] != '':
                    if self.enemy['ADC'] != '':
                        reccs = self.enemy['ADC'].role_counters_sorted[:k]
                        self.print_reccs(reccs, f"Champion Recommendation Against Enemy {self.enemy['ADC'].name}", reverse_winrate=True)
                        return reccs
                    reccs = self.ally['Support'].partner_synergies_sorted[:k]
                    self.print_reccs(reccs, f"Champion Recommendation With Ally {self.ally['Support'].name}")
                    return reccs
                if self.enemy['Support'] != '':
                    reccs = self.enemy['Support'].partner_counters_sorted[:k]
                    self.print_reccs(reccs, f"Champion Recommendation Against Enemy {self.enemy['Support'].name}", reverse_winrate=True)
                    return reccs


    def predict(self):
        winrate = [None] * 5
        print("Matchup Predictions:")
        games, winrate[0] = self.ally['Top'].role_counters[self.enemy['Top'].name]
        print(f"Top ({self.ally['Top'].name} vs {self.enemy['Top'].name}): {winrate[0]}% ({games})")
        games, winrate[1] = self.ally['Jungle'].role_counters[self.enemy['Jungle'].name]
        print(f"Jungle ({self.ally['Jungle'].name} vs {self.enemy['Jungle'].name}): {winrate[1]}% ({games})")
        games, winrate[2] = self.ally['Middle'].role_counters[self.enemy['Middle'].name]
        print(f"Middle ({self.ally['Middle'].name} vs {self.enemy['Middle'].name}): {winrate[2]}% ({games})")
        games, winrate[3] = self.ally['ADC'].role_counters[self.enemy['ADC'].name]
        print(f"ADC ({self.ally['ADC'].name} vs {self.enemy['ADC'].name}): {winrate[3]}% ({games})")
        games, winrate[4] = self.ally['Support'].role_counters[self.enemy['Support'].name]
        print(f"Support ({self.ally['Support'].name} vs {self.enemy['Support'].name}): {winrate[4]}% ({games})")
        print(f"Average Winrate: {round(sum(winrate) / len(winrate), 2)}%")
        print()


def download_winrates():
    with open("champion_list.txt", 'r') as f:
        champs = f.read().split('\n')
    for champion in tqdm.tqdm(champs):
        Champion(champion)


if __name__ == "__main__":
    download_winrates()
    ally = {
        'Top':     'nasus',
        'Jungle':  'trundle',
        'Middle':  'yasuo',
        'ADC':     'caitlyn',
        'Support': 'nautilus',
    }
    enemy = {
        'Top':     'ornn',
        'Jungle':  'hecarim',
        'Middle':  'cassiopeia',
        'ADC':     'lucian',
        'Support': 'karma',
    }
    matchup = Matchup(ally, enemy)
    matchup.recommend('Support', k=10, verbose=True)
    matchup.predict()
