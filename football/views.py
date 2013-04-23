from pyramid.response import Response
from pyramid.view import view_config

from sqlalchemy.exc import DBAPIError

from pyramid.httpexceptions import HTTPFound
from pyramid.url import route_url

from .models import *

import os 
import csv
import sys
import datetime

@view_config(route_name='home', renderer='templates/home.pt')
def home_view(request):
    return {}

@view_config(route_name='import', renderer='templates/import.pt')
def import_view(request):
    params = request.GET

    if ("file" in params):
      with open (os.getcwd() + '/football/csv/' + params["file"], 'rb') as f:
        dr = csv.DictReader(f)
        for row in dr:
          off_team = get_or_create(DBSession, Team, name=row["off"], short_name=row["off"], season_year=row["season"])
          def_team = get_or_create(DBSession, Team, name=row["def"], short_name=row["def"], season_year=row["season"])

          game_date = datetime.strptime(row["gameid"][0:7], '%Y%md%d')
          #game = get_or_create(DBSession, Game, date=game_date, off

      return {"file": row}
    else:
      return {"file": "none"}

def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        return instance

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

