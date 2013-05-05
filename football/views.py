from pyramid.response import Response
from pyramid.view import view_config

from sqlalchemy.exc import DBAPIError

from pyramid.httpexceptions import HTTPFound
from pyramid.url import route_url

from .models import *

import os 
import csv
import sys
from datetime import datetime, date
from pykov import *

@view_config(route_name='home', renderer='templates/home.pt')
def home_view(request):
    return {}

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
            teamstrings.append("Kickoff")
          if row.play_type == "PAT":
            teamstrings.append("PAT")
            teamstrings.append("Kickoff")
          if row.play_type == "2PT":
            teamstrings.append("2PT")
            teamstrings.append("Kickoff")
          if row.play_type == "Punt":
            teamstrings.append("Punt")      
      p, P = maximum_likelihood_probabilities(tuple(teamstrings),lag_time=1, separator='0')
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

    return {"simulation":simulation.simulation_id} 

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

