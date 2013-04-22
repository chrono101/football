from pyramid.response import Response
from pyramid.view import view_config

from sqlalchemy.exc import DBAPIError

from pyramid.httpexceptions import HTTPFound
from pyramid.url import route_url

from .models import *

@view_config(route_name='home', renderer='templates/home.pt')
def home_view(request):
    try: 
        ksu = DBSession.query(Team).filter(Team.name == "K-State").first()
    except DBAPIError:
        return Response(conn_err_msg, content_type="text/plain", status_int=500)
    return {'team': ksu}

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

