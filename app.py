from flask import Flask, render_template, request, redirect
import requests

import ipl

# urllib3 1.26.6, requests 2.31.0
app = Flask(__name__)

teams =None

@app.route('/')
def home():
    # global teams
    # responce = requests.get('http://127.0.0.1:5000/api/team')
    # teams = sorted(responce.json()['teams'])
    # return render_template('index.html',teams=sorted(teams))
    return render_template('home.html')

@app.route('/navigate')
def navigation():
    route = request.args.get('route')
    if route == "team_names":
        return redirect('/teams')  # Redirect to the appropriate route
    elif route == "team_details":
        return redirect('/teamdetailinput')
    elif route == "team_vs_team":
        return redirect('/teamvteam')
    elif route == "batter_record":
        return redirect('/batter_record')
    elif route == "bowler_record":
        return redirect('/bowler_record')
    else:
        return "Invalid Selection", 400


@app.route('/batter_record')
def batterRecord():
    batter = request.args.get('batter')
    response = ipl.batterAPI(batter)

    teams = ipl.teamsAPI()['batter']
    return render_template('batter.html', result=response, teams=sorted(teams))


@app.route('/bowler_record')
def bowlerRecord():

    bowler = request.args.get('bowler')
    # response = requests.get('http://127.0.0.1:5000/api/bowler-record?bowler_name={}'.format(bowler))
    # response = response.json()
    response = ipl.bowlerApi(bowler)

    teams = ipl.teamsAPI()['bowler']
    return render_template('bowler.html', result=response, teams=sorted(teams))

@app.route('/teams')
def teams():
    # responce = requests.get('http://127.0.0.1:5000/api/team')
    # teams = responce.json()['teams']
    teams = ipl.teamsAPI()['teams']

    return render_template('teams.html',team = sorted(teams))


@app.route('/teamdetailinput')
def teamDetailinput():
    teams = ipl.teamsAPI()['teams']
    return render_template('teamDetail.html', teams = sorted(teams))

@app.route('/teamdetail')
def teamdetail():
    team = request.args.get('teams')
    response = ipl.teamDetail(team)
    #response = response.json()

    teams = ipl.teamsAPI()['teams']

    return render_template('teamDetail.html', result = response, teams = sorted(teams))


@app.route('/teamvteam')
def team_v_team():

    team1 = request.args.get('team1')
    team2 = request.args.get('team2')
    # response = requests.get('http://127.0.0.1:5000/api/teamComparison?team1={}&team2={}'.format(team1,team2))
    # response=response.json()
    response = ipl.teamVsTeam(team1,team2)

    teams = ipl.teamsAPI()['teams']
    return render_template('index.html',result = response, teams=sorted(teams))

app.run()