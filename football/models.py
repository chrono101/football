from sqlalchemy import *

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
    name = Column(String(255), unique=True)
    short_name = Column(String(255))
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
    play_type = Column(String(255))
    score_difference = Column(Integer)

    def __init__(self, game_id, offensive_team_id, defensive_team_id, down, distance_to_go, yard_line, quarter, seconds_remaining, simulated, play_type, score_difference):
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
        self.score_difference = score_difference 
    
    def __str__(self):
      retval = "[PLAY] G:{} OFF:{} DEF:{} DDT:{}/{}/{} QS:{}/{} ScoreDiff: {} Simulated:{} Type:{}".format(
          self.game_id,
          self.offensive_team_id,
          self.defensive_team_id,
          self.down,
          self.distance_to_go,
          self.yard_line,
          self.quarter,
          self.seconds_remaining,
          self.score_difference,
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
        retval = "[GAME] Date:{} HTID:{} ATID:{} Score:{}-{} Simulated:{}".format(
            self.date,
            self.home_team_id,
            self.away_team_id,
            self.home_team_score,
            self.away_team_score,
            self.simulated
            )
        return retval

'''
class Simulation
Defines a simulation of a football game between two teams
'''
class Simulation(Base):
    __tablename__ = 'simulations'
    simulation_id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey("games.game_id"), nullable=False)
    home_team_chain = Column(PickleType)
    away_team_chain = Column(PickleType)

    def __init__(self, game_id, home_team_chain, away_team_chain):
        self.game_id = game_id
        self.home_team_chain = home_team_chain
        self.away_team_chain = away_team_chain

    def __str__(self):
        retval = "[SIMULATION] SID:{} GID:{}\nHT CHAIN: {}\n AT CHAIN: {}".format(
            self.simulation_id,
            self.game_id,
            self.home_team_chain,
            self.away_team_chain
            )
        return retval

'''
class Simulation Node
Defines a node in the simulation graph
'''
class SimulationNode(Base):
    __tablename__ = 'simulation_nodes'
    simulation_node_id = Column(Integer, primary_key=True)
    simulation_id = Column(Integer, ForeignKey("simulations.simulation_id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.team_id"), nullable=False)
    down = Column(Integer)
    distance_to_go = Column(Integer)
    yard_line = Column(Integer)
    quarter = Column(Integer)
    seconds_remaining = Column(Integer)
    score_difference = Column(Integer)
    count = Column(Integer)

    def __init__(self, simulation_id, team_id, down, distance_to_go, yard_line, quarter, seconds_remaining, score_difference, count):
        self.simulation_id = simulation_id
        self.team_id = team_id
        self.down = down
        self.distance_to_go = distance_to_go
        self.yard_line = yard_line
        self.quarter = quarter
        self.seconds_remaining = seconds_remaining
        self.score_difference = score_difference

    def __str__(self): 
        retval = "[NODE] NID:{} SID:{} TID:{} DDT:{}/{}/{} QS:{}/{} Score Diff:{} Count:{}".format(
            self.simulation_node_id,
            self.simulation_id,
            self.team_id,
            self.down,
            self.distance_to_go,
            self.yard_line,
            self.quarter,
            self.seconds_remaining,
            self.score_difference,
            self.count
            )
        return retval
