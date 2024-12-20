import pandas as pd
import numpy as np
import json

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)


matches = pd.read_csv("matches.csv")
balls = pd.read_csv('deliveries.csv')

ballMatch = balls.merge(matches,how='inner',left_on='match_id',right_on='id')
batter_data = ballMatch[np.append(balls.columns.values, ['player_of_match'])]
bowler_data = batter_data.copy()

def teamNameModification(x):
    if x=='Royal Challengers Bangalore' or x=='Royal Challengers Bengaluru':
        return 'Royal Challengers Bangalore'
    elif x=='Gujarat Titans' or x=='Gujarat Lions':
        return 'Gujarat Titans'
    elif x=='Rising Pune Supergiants' or x=='Rising Pune Supergiant' or x=='Pune Warriors':
        return 'Rising Pune Supergiant'
    elif x=='Delhi Daredevils' or x=='Delhi Capitals':
        return 'Delhi Capitals'
    elif x=='Kings XI Punjab' or x=='Punjab Kings':
        return 'Punjab Kings'
    elif x=='Deccan Chargers' or x=='Sunrisers Hyderabad':
        return 'Sunrisers Hyderabad'
    return x

matches['team1'] = matches['team1'].apply(teamNameModification)
matches['team2'] = matches['team2'].apply(teamNameModification)

def teamsAPI():
    teams= list(set(list(matches['team1'])+list(matches['team2'])))
    batter = list(balls.batter.unique())
    bowler = list(balls.bowler.unique())
    team_dict = {
        'teams':teams,
        'batter' : batter,
        'bowler': bowler
    }
    return team_dict

def teamVsTeam(team1,team2):

    mch = matches[((matches['team1'] == team1) & (matches['team2'] == team2)) | (
                (matches['team1'] == team2) & (matches['team2'] == team1))]

    tot_match = mch.shape[0]

    team1_win = mch[mch['winner'] == team1].shape[0]
    team2_win = mch[mch['winner'] == team2].shape[0]
    draw = tot_match - team1_win - team2_win

    respond = {
        'Total matches': tot_match,
        team1: team1_win,
        team2: team2_win,
        'Draw': draw
    }

    return respond

def overallTeam(team_name):
    df=matches[(matches['team1']==team_name) | (matches['team2']==team_name)].copy()
    tot_match = df.shape[0]
    won = df[df.winner == team_name].shape[0]
    nr = df[df.winner.isnull()].shape[0]
    loss = tot_match - won - nr
    title = matches[(matches['match_type'] == 'Final') & (matches['winner'] == team_name)].shape[0]

    respond = {
        'tot_match': tot_match,
        'win': won,
        'loss': loss,
        'No Result': nr,
        'title':title
    }

    return  respond

def teamDetail(team_name):

    teams = teamsAPI()
    against={}
    for i in teams['teams']:
        if i == team_name:
            overall = overallTeam(team_name)
        else:
            against[i]= teamVsTeam(team_name,i)

    respond = {
        team_name:{
            'overall': overall,
            'against':against}
    }
    return respond


def bowlerRun(x):
    if x[0] in ['penalty', 'legbyes', 'byes']:
        return 0
    else:
        return x[1]

bowler_data['bowler_run'] = bowler_data[['extras_type', 'total_runs']].apply(bowlerRun, axis=1)


def bowlerWicket(x):
    if x[0] in ['caught', 'caught and bowled', 'bowled', 'stumped', 'lbw', 'hit wicket']:
        return x[1]
    else:
        return 0

bowler_data['isBowlerWicket'] = bowler_data[['dismissal_kind', 'is_wicket']].apply(bowlerWicket, axis=1)


def bowlerRecord(bowler, df):
    df = df[df['bowler'] == bowler]
    tot_inning = df.match_id.nunique()  # 1
    tot_wicket = df.isBowlerWicket.sum()  # 2
    tot_run = df.bowler_run.sum()
    tot_ball = df[~df.extras_type.isin(['wides', 'noballs'])].shape[0]
    tot_over = tot_ball / 6

    if tot_over:
        eco = round(tot_run / tot_over, 2)  # 3
    else:
        eco = 0

    if tot_wicket:
        avg = round(tot_run / tot_wicket, 2)  # 4
        str_rate = round(tot_ball*100 / tot_wicket, 2)  # 5
    else:
        avg = 0
        str_rate = 0

    fours = df[df['bowler_run'] == 4].shape[0]
    sixes = df[df['bowler_run'] == 6].shape[0]

    grp = df.groupby('match_id')['is_wicket'].sum()

    w3 = grp[grp.values >= 3].count()

    mom = df[df.player_of_match == bowler].drop_duplicates(['match_id'], keep='first').shape[0]

    data = {
        'innings': tot_inning,
        'wicket': tot_wicket,
        'economy': eco,
        'average': avg,
        'strikeRate': str_rate,
        'fours': fours,
        'sixes': sixes,
        '3+W': w3,
        'mom': mom
    }

    return data

def bowlerAgainst(bowler, df, team):
    df=df[df['batting_team'] == team]
    return bowlerRecord(bowler, df)


def bowlerApi(bowler, balls = bowler_data):
    df = balls[balls.inning.isin([1, 2])]
    selfRecord = bowlerRecord(bowler, df)
    team = teamsAPI()
    against = {i: bowlerAgainst(bowler, df, i) for i in team['teams']}

    data = {
        bowler: {
            'all': selfRecord,
            'against': against
        }
    }
    return data


def batsmanRecord(batsman, df):
    inning = df.match_id.nunique()
    runs = df.batsman_runs.sum()
    fours = df[df.batsman_runs == 4].shape[0]
    sixes = df[df.batsman_runs == 6].shape[0]
    tot_balls = df[~df.extras_type.isin(['wides', 'noballs'])].shape[0]
    if tot_balls:
        str_rate = round(runs * 100 / tot_balls, 2)
    else:
        str_rate = 0

    grp = df.groupby('match_id')['is_wicket'].sum()
    nout = grp[grp.values == 0].count()

    if (inning - nout):
        avg = round(runs / (inning - nout), 2)
    else:
        avg = 0

    aggrun = df.groupby('match_id')['batsman_runs'].sum()

    fifties = aggrun[aggrun.values >= 50].count()
    hundreds = aggrun[aggrun.values >= 100].count()
    maxrun = aggrun.max()
    mom = df[df.player_of_match == batsman].drop_duplicates('match_id', keep='first').shape[0]

    data = {
        'inning': inning,
        'runs': runs,
        'fours': fours,
        'sixes': sixes,
        'strikeRate': str_rate,
        'average': avg,
        'Not Out': nout,
        'Fifties': fifties,
        'Hundred': hundreds,
        'Higest run': maxrun,
        'MoM': mom
    }
    return data

def batterAgainst(batsman,df,i):
    df = df[df.bowling_team==i]
    return batsmanRecord(batsman,df)


def batterAPI(batsman, bats=batter_data):
    df = bats[bats.inning.isin([1, 2])]
    df = df[df['batter'] == batsman]
    selfRecord = batsmanRecord(batsman, df)

    team = teamsAPI()
    against = {i: batterAgainst(batsman, df, i) for i in team['teams']}

    data = {
        batsman: {
            'all': selfRecord,
            'against': against
        }
    }

    return data

