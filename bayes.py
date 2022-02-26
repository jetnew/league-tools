import numpy as np
import pandas as pd
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.metrics import accuracy_score, mean_absolute_error
from sklearn.impute import KNNImputer

df = pd.read_csv("matches.csv", index_col=[0])

players = [f'player{i}' for i in range(10)]

X1 = df[players]
X1['win'] = 1
X2 = df[players].copy()
X2[players] = X2[players[5:] + players[:5]]
X2['win'] = 0
X = pd.concat((X1, X2), ignore_index=True)
X.rename(columns={
    'player0': 'top1',
    'player1': 'jg1',
    'player2': 'mid1',
    'player3': 'adc1',
    'player4': 'sp1',
    'player5': 'top2',
    'player6': 'jg2',
    'player7': 'mid2',
    'player8': 'adc2',
    'player9': 'sp2',
}, inplace=True)

def cond_prob(role, champion, win):
    return len(X[(X[role] == champion) & (X['win'] == win)]) / len(X[X['win'] == win])

def count(role, champion):
    return len(X[X[role] == champion])

def compute_prob(match, played_at_least=3):
    # Ref: https://jonathanweisberg.org/vip/multiple-conditions.html
    win, lose = 0.5, 0.5
    for role, champion in match.items():
        if champion != '' and count(role, champion) >= played_at_least:
            win *= cond_prob(role, champion, 1)
            lose *= cond_prob(role, champion, 0)
    if win + lose == 0:
        return 0
    return win / (win + lose)


def recommend_champion(match, role, played_at_least=5):
    champions = X[role].unique()
    predicted_winrates = []
    for champion in champions:
        if count(role, champion) < played_at_least:
            continue
        test_match = match.copy()
        test_match[role] = champion
        prob = compute_prob(test_match, played_at_least)
        predicted_winrates.append((champion, prob))
    rankings = sorted(predicted_winrates, key=lambda x: x[1], reverse=True)
    winning = list(filter(lambda x: x[1] <= 0.5, rankings))
    recommendations = winning if len(winning) < 10 else rankings[:10]
    print(f"Recommending for {role}:")
    for champion, winrate in recommendations:
        print(f"{champion} (WR: {winrate:.2f})")


match = {
    'top1': 'Shen',
    'jg1': 'MasterYi',
    'mid1': 'VelKoz',
    'adc1': 'Lucian',
    'sp1': '',
    'top2': 'Tryndamere',
    'jg2': 'LeeSin',
    'mid2': 'Yasuo',
    'adc2': 'KaiSa',
    'sp2': 'Janna',
}

recommend_champion(match, 'sp1')