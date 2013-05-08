from pyramid.response import Response
from pyramid.view import view_config

from sqlalchemy.exc import DBAPIError

from pyramid.httpexceptions import HTTPFound
from pyramid.url import route_url

from .models import *

from datetime import datetime, date
from pykov import *
from random import *
import numpy as np
import os 
import csv
import sys

@view_config(route_name='home', renderer='templates/home.pt')
def home_view(request):
    simulations = DBSession.query(Simulation).all()
    gamestrings = dict()
    for row in simulations:
      game = DBSession.query(Game).filter_by(game_id=row.game_id).first()
      home_team = DBSession.query(Team).filter_by(team_id=game.home_team_id).first()
      away_team = DBSession.query(Team).filter_by(team_id=game.away_team_id).first()

      gamestrings[row.simulation_id] = "{} {} @ {} {}".format(
          away_team.season_year,
          away_team.name,
          home_team.season_year,
          home_team.name
          )
    

    
    return {"simulations":simulations, "gamestrings":gamestrings}

@view_config(route_name='import', renderer='templates/import.pt')
def import_view(request):
    params = request.GET

    def get_or_create(session, model, **kwargs):
      instance = session.query(model).filter_by(**kwargs).first()
      if instance:
        return instance
      else:
        instance = model(**kwargs)
        return instance


    if ("file" in params):
      with open (os.getcwd() + '/football/csv/' + params["file"], 'rb') as f:
        dr = csv.DictReader(f)
        rows_processed = 0
        for row in dr:
          # Create Team Objects
          off_team = get_or_create(DBSession, Team, name=row["off"], short_name=row["off"], season_year=row["season"])
          def_team = get_or_create(DBSession, Team, name=row["def"], short_name=row["def"], season_year=row["season"])
          DBSession.add(off_team)
          DBSession.add(def_team)

          # Create Game Object
          gameidstr = row["gameid"]
          game_date = datetime.strptime(gameidstr[0:8], '%Y%m%d')
          game_date = game_date.date()
          hometeamstr = gameidstr[gameidstr.index('@')+1:]
          awayteamstr = gameidstr[gameidstr.index('_')+1:gameidstr.index('@')]

          home_team = DBSession.query(Team).filter_by(name=hometeamstr).first()
          away_team = DBSession.query(Team).filter_by(name=awayteamstr).first()

          if home_team.name is off_team.name:
            homescore = row["offscore"]
            awayscore = row["defscore"]
          else:
            homescore = row["defscore"]
            awayscore = row["offscore"]

          game = DBSession.query(Game).filter_by(
              home_team_id=home_team.team_id,
              away_team_id=away_team.team_id,
              simulated=False,
              date=game_date
              ).first()
          if game:
               game.home_team_score = homescore
               game.away_team_score = awayscore
          else:
            game = Game(
                home_team_id = home_team.team_id,
                away_team_id = away_team.team_id,
                home_team_score = homescore,
                away_team_score = awayscore,
                simulated=False,
                date=game_date
                )               

          DBSession.add(game)
          DBSession.flush()          

          # Creates Play Object
          try: 
            seconds = (int(row["min"]) * 60) + int(row["sec"])
          except ValueError:
            seconds = (60 * 60)

          if "TOUCHDOWN" in row["description"]:
            playtypestr = "Touchdown"
          elif "extra point is GOOD" in row["description"]:
            playtypestr = "PAT"
          elif "extra point is Blocked" in row["description"]:
            playtypestr = "Blocked"
          elif "BLOCKED" in row["description"]:
            playtypestr = "Blocked"
          elif "ATTEMPT SUCCEEDS" in row["description"]:
            playtypestr = "2PT"
          elif "FUMBLES" in row["description"]:
            playtypestr = "Turnover"
          elif "INTERCEPTED" in row["description"]:
            playtypestr = "Turnover"
          elif "field goal is GOOD" in row["description"]:
            playtypestr = "FG"
          elif "SAFETY" in row["description"]:
            playtypestr = "Safety"
          elif "punts" in row["description"]:
            playtypestr = "Punt"
          else:
            playtypestr = "Unknown"
          

          play = get_or_create(
              DBSession,
              Play,
              game_id=game.game_id,
              offensive_team_id=off_team.team_id,
              defensive_team_id=def_team.team_id,
              down=row["down"],
              distance_to_go=row["togo"],
              yard_line=row["ydline"],
              quarter=row["qtr"],
              seconds_remaining=seconds,
              simulated=False,
              play_type=playtypestr,
              score_difference=int(row["scorediff"])
              )

          DBSession.add(play)
          DBSession.flush()

          # Increment Counter
          rows_processed += 1
      return {"file": row, "home": hometeamstr, "away":awayteamstr, "rows_processed":rows_processed, "date":game_date }
    else:
      return {"file": "none"}

@view_config(route_name='create_simulation', renderer='templates/createsim.pt')
def createsim_view(request):
    params = request.GET
    team1_id = params["team1"]
    team2_id = params["team2"]

    def get_or_create(session, model, **kwargs):
      instance = session.query(model).filter_by(**kwargs).first()
      if instance:
        return instance
      else:
        instance = model(**kwargs)
        return instance

    def roundN(x, base=5):
        return int(base * round(float(x)/base))

    def toGoString(x):
      if 1 <= x <= 3:
        return "S"
      elif 4 <= x <= 10:
        return "M"
      elif 11 <= x <= 99:
        return "L"
      else:
        return "Unknown"

    def createChain(team_id):
      teamstrings = []
      team = DBSession.query(Play).filter(Play.offensive_team_id==team_id).all()
      for row in team:
          if row.down != 0:
            statestring = "{}{}{}".format(
                row.down,
                toGoString(row.distance_to_go),
                roundN(row.yard_line, 10),
                )
            teamstrings.append(statestring)
          if row.play_type == "Touchdown":
            teamstrings.append(row.play_type)
          if row.play_type == "FG":
            teamstrings.append("FG")
            teamstrings.append("EOD")
          if row.play_type == "PAT":
            teamstrings.append("PAT")
            teamstrings.append("EOD")
          if row.play_type == "2PT":
            teamstrings.append("2PT")
            teamstrings.append("EOD")
          if row.play_type == "Punt":
            teamstrings.append("Punt")
            teamstrings.append("EOD")
          if row.play_type == "Turnover":
            teamstrings.append("Turnover")
            teamstrings.append("EOD")
      p, P = maximum_likelihood_probabilities(tuple(teamstrings),lag_time=1, separator='EOD')
      return p, P

    c1, C1 = createChain(team1_id)
    c2, C2 = createChain(team2_id)
    
    game = get_or_create(
        DBSession,
        Game,
        home_team_id=team1_id, 
        away_team_id=team2_id,
        home_team_score=0,
        away_team_score=0,
        simulated=True,
        date=date.today()
        )

    DBSession.add(game)
    DBSession.flush()

    simulation = get_or_create(
        DBSession, 
        Simulation,
        game_id=game.game_id,
        home_team_chain=C1,
        away_team_chain=C2
        )
        
    DBSession.add(simulation)
    DBSession.flush()

    return {"simulation":C1} 

@view_config(route_name='simulate', renderer='templates/simulate.pt')
def simulate_view(request):
    params = request.GET
    simulation_id = params["sid"]
    simulations = params["n"]

    simulation = DBSession.query(Simulation).filter(Simulation.simulation_id==simulation_id).first()
    game = DBSession.query(Game).filter(Game.game_id==simulation.game_id).first()
    home_team = DBSession.query(Team).filter(Team.team_id==game.home_team_id).first()
    away_team = DBSession.query(Team).filter(Team.team_id==game.away_team_id).first()

    teams = [home_team, away_team]
    chains = [simulation.home_team_chain, simulation.away_team_chain]
    scores = {0:dict(), 1:dict()}
    overunders = list()
    wins = {0:0, 1:0}

    output_log = dict()
    avg_time_per_play = 30
    default_state = '1M80'    
    i = 0

    while i < int(simulations):
        logkey = "sim"+str(i)        
        output_log[logkey+"-pbp"] = list()

        last_state = default_state
        
        curteam = randrange(0,2)

        scores[0][i] = 0
        scores[1][i] = 0
        
        # 3600 seconds = 1 hour = 4 * 15-minute quarters
        gameclock = 3600
       
        output_log[logkey+"-pbp"].append(teams[curteam].name + ":" + default_state)       
        while gameclock >= 0:
            # Move from the last state
            current_state = chains[curteam].move(last_state)
            output_log[logkey+"-pbp"].append(teams[curteam].name + ":" + current_state)
            
            # If a special state, take action
            if current_state == "Touchdown":
                scores[curteam][i] = scores[curteam][i] + 6
                last_state = current_state
            elif current_state == "FG":
                scores[curteam][i] = scores[curteam][i] + 3
                curteam = int(not bool(curteam))
                output_log[logkey+"-pbp"].append(teams[curteam].name + ":" + default_state)
                last_state = default_state
            elif current_state == "2PT":
                scores[curteam][i] = scores[curteam][i] + 2
                curteam = int(not bool(curteam))
                output_log[logkey+"-pbp"].append(teams[curteam].name + ":" + default_state)
                last_state = default_state
            elif current_state == "PAT":
                scores[curteam][i] = scores[curteam][i] + 1
                curteam = int(not bool(curteam))
                output_log[logkey+"-pbp"].append(teams[curteam].name + ":" + default_state)
                last_state = default_state
            elif current_state == "Punt":
                curteam = int(not bool(curteam))
                output_log[logkey+"-pbp"].append(teams[curteam].name + ":" + default_state)
                last_state = default_state
            elif current_state == "Turnover":
                curteam = int(not bool(curteam))
                # Change staate to spot of the ball
                last_state = "1M" + str(100-int(last_state[2:]))
                output_log[logkey+"-pbp"].append(teams[curteam].name + ":" + last_state)
            else:
                last_state = current_state
   
            # Take time off the clock
            gameclock = gameclock - avg_time_per_play       
        
        output_log[logkey+"-pbp"].append("FINAL SCORE: {} - {} {} - {}".format(
            teams[0].name,
            scores[0][i],
            teams[1].name,
            scores[1][i]))
        if scores[0][i] > scores[1][i]:
          wins[0] = wins[0] + 1
        elif scores[0][i] < scores[1][i]:
          wins[1] = wins[1] + 1
        else:
          pass
        overunders.append(scores[0][i] + scores[1][i])
        i = i+1
    over_under = np.mean(overunders)
    home_avg_score = np.mean(scores[0].values())
    away_avg_score = np.mean(scores[1].values())
    ties = (int(simulations)-(wins[0]+wins[1]))
    if home_avg_score > away_avg_score:
        line = "{} by {}".format(home_team.name, round(home_avg_score-away_avg_score))
    elif home_avg_score < away_avg_score:
        line = "{} by {}".format(away_team.name, round(away_avg_score-home_avg_score))
    else:
        line = "{} and {} tie at {}".format(home_team.name, away_team.name, home_avg_score)
    return {
      "home_team":home_team.name,
      "away_team":away_team.name,
      "simulations":simulations,
      "game_log":output_log, 
      "wins":wins, 
      "ties":ties,
      "ties_percentage":round(100*ties/float(simulations), 2),
      "home_team_percentage":round(100*wins[0]/float(simulations), 2),
      "away_team_percentage":round(100*wins[1]/float(simulations), 2),
      "overunder":over_under, 
      "line":line,
      "home_avg_score":round(home_avg_score, 2),
      "away_avg_score":round(away_avg_score, 2)
      }

conn_err_msg = """\
Pyramid is having a problem using your SQL database.  The problem
might be caused by one of the following things:

1.  You may need to run the "initialize_football_db" script
    to initialize your database tables.  Check your virtual 
    environment's "bin" directory for this script and try to run it.

2.  Your database server may not be running.  Check that the
    database server referred to by the "sqlalchemy.url" setting in
    your "development.ini" file is running.

After you fix the problem, please restart the Pyramid application to
try it again.
"""

