from sqlalchemy import (
    Column,
    Integer,
    Text,
    Boolean,
    )

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

'''
class Team
Defines a football team.
'''
class Team(Base):
    __tablename__ = 'teams'
    team_id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)
    short_name = Column(Text)
    season_year = Column(Integer)

    def __init__(self, name, short_name, season_year):
        self.name = name
        self.short_name = short_name
        self.season_year = season_year

    def __str__(self):
        retval = "[TEAM] {}/{} Y:{} ID:{}".format(
            self.name,
            self.short_name,
            self.season_year,
            self.team_id
            )
        return retval

'''
class Play
Defines a football play
'''
class Play(Base):
    __tablename__ = 'plays'
    play_id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey("games.game_id"), nullable=False)
    offensive_team_id = Column(Integer, ForeignKey("teams.team_id"), nullable=False)
    defensive_team_id = Column(Integer, ForeignKey("teams.team_id"), nullable=False)
    down = Column(Integer)
    distance_to_go = Column(Integer)
    yard_line = Column(Integer)
    quarter = Column(Integer)
    seconds_remaining = Column(Integer)
    simulated = Column(Boolean)
    play_type = Column(Text)

    def __init__(self, game_id, offensive_team_id, defensive_team_id, down, distance_to_go, yard_line, quarter, seconds_remaining, simulated, play_type):
        self.game_id = game_id
        self.offensive_team_id = offensive_team_id
        self.defensive_team_id = defensive_team_id
        self.down = down
        self.distance_to_go = distance_to_go
        self.yard_line = yard_line
        self.quarter = quarter
        self.seconds_remaining = seconds_remaining
        self.simulated = simulated
        self.play_type = play_type
    
    def __str__(self):
      retval = "[PLAY] G:{} OFF:{} DEF:{} DDT:{}/{}/{} QS:{}/{} Simulated:{} Type:{}".format(
          self.game_id,
          self.offensive_team_id,
          self.defensive_team_id,
          self.down,
          self.distance_to_go,
          self.yard_line,
          self.quarter,
          self.seconds_remaining,
          self.simulated,
          self.play_type
          )

      return retval
      
'''
class Game
Defines a football game
'''
class Game(Base):
    __tablename__ = 'games'
    game_id = Column(Integer, primary_key=True)
    home_team_id = Column(Integer, ForeignKey("teams.team_id"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("teams.team_id"), nullable=False)
    home_team_score = Column(Integer)
    away_team_score = Column(Integer)
    simulated = Column(Boolean)
    date = Column(Date)

    def __init__(self, home_team_id, away_team_id, home_team_score, away_team_score, simulated, date):
        self.home_team_id = home_team_id
        self.away_team_id = away_team_id
        self.home_team_score = home_team_score
        self.away_team_score = away_team_score
        self.simulated = simulated
        self.date = date

    def __str__(self):
        retval = "[GAME] Date:{} HTID:{} ATID:{} SCORE:{}-{} Simulated:{}".format(
            self.date
            self.home_team_id
            self.away_team_id
            self.home_team_score
            self.away_team_score
            self.simulated
            )
