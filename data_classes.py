
import enum
import time

# TODO map_stat_ids->map_stats_ids
# TODO make sure toString methods can support links being integers (in general standardize the capitalization)

class AllData:
	def __init__(self, divisions = dict(), teams = dict(), players = dict(), matches = dict()):
		# Indexed by the objects ID
		self.divisions = divisions
		self.teams     = teams
		self.players   = players
		self.matches   = matches

class Scale(enum.Enum):
	ESSENTIAL = 1
	FULL      = 2

# Helper function
def listToString(vals, separator = ',', map_func = str):
	return separator.join(map(map_func, vals))

class Division(object):
	def __init__(self, name = None, id_num = None, abbrev = None, teams = None, team_ids = None):
		self.scale = Scale.FULL
		
		# Essential Data
		self.name   = str(name)
		self.id_num = int(id_num)
		self.abbrev = str(abbrev)

		# Links to the Teams in this Division. self.teams is a dict() with keys of the team's id and the value is the Team.
		# TODO make this check better
		if teams is None and team_ids is None:
			# If neither case is given, then self.teams defaults to an empty dict.
			self.teams = dict()
		elif type(teams) is dict and team_ids is None:
			# If the teams dict is given, use that.
			self.teams = teams
		elif type(team_ids) in [list, str] and teams is None:
			if type(team_ids) is str:
				# If team_ids is a str, then try to parse it as a ',' separated list of values.
				team_ids = team_ids.split(',')

			# If the list of team_ids is given, then use the values as keys in the self.teams dict(). Set all values in self.teams to None.
			self.teams = {int(v):None for v in team_ids}
		else:
			raise Exception('Unexpected team data given: teams->' + str(teams) + ', team_ids->' + str(team_ids))

	def getFullString(self, separator, equal_symbol):
		if self.scale != Scale.FULL:
			raise Exception('Cannot get full string for non-full division')

		values = [('name', self.name), ('id_num', self.id_num), ('abbrev', self.abbrev), ('team_ids', listToString(self.teams.keys()))]

		return separator.join(map(lambda x: str(x[0]) + equal_symbol + str(x[1]), values))

	def __str__(self):
		if self.name is None:
			raise Exception('Division has no name')

		rv = str(self.name)

		if self.abbrev is not None:
			rv += ' (' + str(self.abbrev) + ')'

		return rv

class Team(object):
	def __init__(self, name = None, id_num = None,
					division = None, division_id = None,
					players = None, player_ids = None,
					matches = None, match_ids = None):
		self.scale = Scale.ESSENTIAL

		# Essential Data
		self.name     = name
		self.id_num   = int(id_num)

		# Links to other data.
		# self.division is the Division this team is in.
		if division is None and division_id is None:
			self.division = None
		elif type(division) is Division and division_id is None:
			self.division = division
		elif type(division_id) in [int, str] and division is None:
			self.division = int(division_id)
		else:
			raise Exception('Unexpected division data given: division->' + str(division) + ', division_id->' + str(division_id))

		# self.players is the Players on this Team. It is a dict() with keys of player's id and values of the Player.
		if players is None and player_ids is None:
			self.players = dict()
		elif type(players) is dict and player_ids is None:
			self.players = players
		elif type(player_ids) in [list, str] and players is None:
			if type(player_ids) is str:
				player_ids = player_ids.split(',')
			self.players = {int(v):None for v in player_ids}
		else:
			raise Exception('Unexpected player data given: players->' + str(players) + ', player_ids->' + str(player_ids))

		# self.matches is the Matches on this Team. It is a dict() with keys of match's id and values of the Match.
		if matches is None and match_ids is None:
			self.matches = dict()
		elif type(matches) is dict and match_ids is None:
			self.matches = matches
		elif type(match_ids) in [list, str] and matches is None:
			if type(match_ids) is str:
				match_ids = match_ids.split(',')
			self.matches = {int(v):None for v in match_ids}
		else:
			raise Exception('Unexpected match data given: matches->' + str(matches) + ', match_ids->' + str(match_ids))

		# Other Data, TODO allow this data to be given in the constructor
		self.abbrev   = None
		self.location = None

		self.logo_url        = None
		self.icon_url        = None
		self.primary_color   = None
		self.secondary_color = None

	def addFullData(self, name = None, id_num = None,
					division_id = None, player_ids = None, match_ids = None,
					abbrev = None, location = None, logo_url = None, icon_url = None, primary_color = None, secondary_color = None):
		if any(v is None for v in [abbrev, location, logo_url, icon_url, primary_color, secondary_color]):
			raise Exception('Must provide all data')

		# TODO check identifying data

		self.scale = Scale.FULL

		self.abbrev   = abbrev
		self.location = location

		self.logo_url        = logo_url
		self.icon_url        = icon_url
		self.primary_color   = primary_color
		self.secondary_color = secondary_color

	def getEssentialString(self, separator, equal_symbol):
		values = [('name', self.name), ('id_num', self.id_num), ('division_id', self.division.id_num),
					('player_ids', listToString(self.players.keys())), ('match_ids', listToString(self.matches.keys()))]

		return separator.join(map(lambda x: str(x[0]) + equal_symbol + str(x[1]), values))

	def getFullString(self, separator, equal_symbol):
		values = [('name', self.name), ('id_num', self.id_num), ('division_id', self.division.id_num),
					('player_ids', listToString(self.players.keys())), ('match_ids', listToString(self.matches.keys())),
					('abbrev', self.abbrev), ('location', self.location),
					('logo_url', self.logo_url), ('icon_url', self.icon_url), ('primary_color', self.primary_color), ('secondary_color', self.secondary_color)]

		return separator.join(map(lambda x: str(x[0]) + equal_symbol + str(x[1]), values))

	def __str__(self):
		if self.name is None:
			raise Exception('Team has no name')

		rv = str(self.name)
		if self.abbrev is not None:
			rv += ' (' + str(self.abbrev) + ')'
		return rv

class Player(object):
	def __init__(self, name = '', id_num = -1, team = None, team_id = None, player_stats = None, player_stat_ids = None):
		self.scale = Scale.ESSENTIAL

		# Essential Data
		self.name   = name
		self.id_num = int(id_num)

		# Links to other data
		if team is None and team_id is None:
			self.team = None
		elif type(team) is Team and team_id is None:
			self.team = team
		elif type(team_id) in [int, str] and team is None:
			self.team = int(team_id)
		else:
			raise Exception('Unexpected team data given: team->' + str(team) + ', team_id->' + str(team_id))

		# Stats for this player for all maps. Indexed by (match_id, map_num, player_id). Values are PlayerStats objects.
		if player_stats is None and player_stat_ids is None:
			self.player_stats = dict()
		elif type(player_stats) is dict and player_stat_ids is None:
			self.player_stats = player_stats
		elif type(player_stat_ids) in [list, str] and player_stats is None:
			if type(player_stat_ids) is str:
				if player_stat_ids == '':
					# TODO handle this edge case better
					player_stat_ids = []
				else:
					player_stat_ids = map(lambda x: tuple(x.split(',')), player_stat_ids.split(';'))
			self.player_stats = {(int(a), int(b), int(c)):None for a, b, c in player_stat_ids}

		# Other data
		self.role   = None
		self.heroes = None
		self.number = None

		self.given_name    = None
		self.family_name   = None
		self.home_location = None
		self.nationality   = None
		self.headshot_url  = None

	def addFullData(self, name = None, id_num = None, team_id = None, player_stat_ids = None,
						role = None, heroes = None, number = None, given_name = None, family_name = None, home_location = None, nationality = None, headshot_url = None):
		self.scale = Scale.FULL

		if any(v is None for v in [role, heroes, number, given_name, family_name, home_location, nationality, headshot_url]):
			raise Exception('Must provide all data')

		self.role   = role
		self.heroes = heroes
		self.number = number

		self.given_name    = given_name
		self.family_name   = family_name
		self.home_location = home_location
		self.nationality   = nationality
		self.headshot_url  = headshot_url

	def getEssentialString(self, separator, equal_symbol):
		values = [('name', self.name), ('id_num', self.id_num), ('team_id', self.team.id_num),
					('player_stat_ids', listToString(self.player_stats.keys(), separator = ';', map_func = listToString))]

		return separator.join(map(lambda x: str(x[0]) + equal_symbol + str(x[1]), values))

	def getFullString(self, separator, equal_symbol):
		values = [('name', self.name), ('id_num', self.id_num), ('team_id', self.team.id_num),
					('player_stat_ids', listToString(self.player_stats.keys(), separator = ';', map_func = listToString)),
					('role', self.role), ('heroes', listToString(self.heroes)), ('number', self.number),
					('given_name', self.given_name), ('family_name', self.family_name),('home_location', self.home_location),
					('nationality', self.nationality), ('headshot_url', self.headshot_url)]

		return separator.join(map(lambda x: str(x[0]) + equal_symbol + str(x[1]), values))

	def __str__(self):
		return self.name

class MatchStatus(enum.Enum):
	CONCLUDED   = 1
	IN_PROGRESS = 2
	PENDING     = 3

def matchStatusFromString(ms_str):
	if ms_str in ['CONCLUDED', str(MatchStatus.CONCLUDED)]:
		return MatchStatus.CONCLUDED

	if ms_str in ['IN_PROGRESS', str(MatchStatus.IN_PROGRESS)]:
		return MatchStatus.IN_PROGRESS

	if ms_str in ['PENDING', str(MatchStatus.PENDING)]:
		return MatchStatus.PENDING

	raise Exception('Unexpected match state string: ' + str(ms_str))

class Match(object):
	def __init__(self, team1 = None, team1_id = None, team2 = None, team2_id = None,
					id_num = -1, stage_num = -1, week_num = -1,
					match_status = None, t1_score = None, t2_score = None,
					scheduled_start = None, actual_start = None, actual_end = None,
					map_stats = None, map_stat_ids = None):
		# Essential data
		if match_status is None or type(match_status) is MatchStatus:
			self.match_status = match_status
		elif type(match_status) is int:
			self.match_status = MatchStatus(match_status)
		elif type(match_status) is str:
			self.match_status = matchStatusFromString(match_status)
		else:
			raise Exception('Unexpected match_status: ' + str(match_status))

		if team1 is None and team1_id is None:
			raise Exception('Must provided a team1 for a Match')
		elif type(team1) is Team and team1_id is None:
			self.team1 = team1
		elif type(team1_id) in [int, str] and team1 is None:
			self.team1 = int(team1_id)
		else:
			raise Exception('Unexpected team1 data given: team1->' + str(team1) + ', team1_id->' + str(team1_id))
		
		if team2 is None and team2_id is None:
			raise Exception('Must provided a team2 for a Match')
		elif type(team2) is Team and team2_id is None:
			self.team2 = team2
		elif type(team2_id) in [int, str] and team2 is None:
			self.team2 = int(team2_id)
		else:
			raise Exception('Unexpected team2 data given: team2->' + str(team2) + ', team2_id->' + str(team2_id))

		self.id_num = int(id_num)

		self.stage_num = int(stage_num)
		self.week_num  = int(week_num)

		if t1_score is None or type(t1_score) is MatchScore:
			self.t1_score = t1_score
		elif type(t1_score) is str:
			self.t1_score = matchScoreFromString(t1_score)
		else:
			raise Exception('Invalid t1_score: ' + str(t1_score))
		
		if t2_score is None or type(t2_score) is MatchScore:
			self.t2_score = t2_score
		elif type(t2_score) is str:
			self.t2_score = matchScoreFromString(t2_score)
		else:
			raise Exception('Invalid t1_score: ' + str(t2_score))

		# Other data
		self.scheduled_start = scheduled_start

		self.actual_start = actual_start
		self.actual_end   = actual_end

		if map_stats is None and map_stat_ids is None:
			self.map_stats = dict()
		elif type(map_stats) is dict and map_stat_ids is None:
			self.map_stats = map_stats
		elif type(map_stat_ids) in [list, str] and map_stats is None:
			if type(map_stat_ids) is str:
				if map_stat_ids == '':
					map_stat_ids = []
				else:
					map_stat_ids = map(lambda x: tuple(x.split(',')), map_stat_ids.split(';'))
			self.map_stats = {(int(a), int(b)):None for a, b in map_stat_ids}
		else:
			raise Exception('Unexpected map_stats data given: map_stats->' + str(map_stats) + ', map_stat_ids->' + str(map_stat_ids))

	def addConcludedData(self, t1_score, t2_score, actual_start, actual_end):
		self.match_status = MatchStatus.CONCLUDED

		self.t1_score = t1_score
		self.t2_score = t2_score

		self.actual_start = actual_start
		self.actual_end   = actual_end

	def addInProgressData(self):
		self.match_status = MatchStatus.IN_PROGRESS

	def addPendingData(self):
		self.match_status = MatchStatus.PENDING

	def getEssentialString(self, separator, equal_symbol):
		# TODO add scheduled_start
		values = [('match_status', self.match_status), ('id_num', self.id_num), ('team1_id', self.team1.id_num), ('team2_id', self.team1.id_num),
					('stage_num', self.stage_num), ('week_num', self.week_num),
					('map_stat_ids', listToString(self.map_stats.keys(), separator = ';', map_func = listToString))]

		if self.match_status == MatchStatus.CONCLUDED:
			values += [('t1_score', self.t1_score), ('t2_score', self.t2_score)]

		return separator.join(map(lambda x: str(x[0]) + equal_symbol + str(x[1]), values))

	def getFullString(self, separator, equal_symbol):
		# TODO output the times in a good way
		values = [('match_status', self.match_status), ('id_num', self.id_num), ('team1_id', self.team1.id_num), ('team2_id', self.team1.id_num),
					('stage_num', self.stage_num), ('week_num', self.week_num), ('scheduled_start', time.asctime(self.scheduled_start)),
					('map_stat_ids', listToString(self.map_stats.keys(), separator = ';', map_func = listToString))]

		if self.match_status == MatchStatus.CONCLUDED:
			values += [('t1_score', self.t1_score), ('t2_score', self.t2_score),
						('actual_start', time.asctime(self.actual_start)), ('actual_end', time.asctime(self.actual_end))]

		return separator.join(map(lambda x: str(x[0]) + equal_symbol + str(x[1]), values))

	def __str__(self):
		str_val = 'Stage ' + str(self.stage_num) + ', Week ' + str(self.week_num) + ', ' + str(self.team1) + ' vs. ' + str(self.team2)

		if self.match_status == MatchStatus.CONCLUDED:
			str_val += ' (' + str(self.t1_score.wins) + '-' + str(self.t2_score) + ')'
		return str_val

def matchScoreFromString(str_val):
	vs = dict(key_value.split(':') for key_value in str_val.split('-'))
	return MatchScore(vs['W'], vs['T'], vs['L'])

class MatchScore(object):
	def __init__(self, wins, ties, losses):
		self.wins   = int(wins)
		self.ties   = int(ties)
		self.losses = int(losses)

	def __str__(self):
		return 'W:' + str(self.wins) + '-T:' + str(self.ties) + '-L:' + str(self.losses)

class MapStats(object):
	def __init__(self, match = None, match_id = None, map_num = None, ow_map_id = None, total_game_time = None,
					t1_player_stats = None, t2_player_stats = None):
		# Link to the match this map was from
		if match is None and match_id is None:
			raise Exception('Must provide a match')
		elif type(match) is Match and match_id is None:
			self.match = match
		elif type(match_id) in [int, str] and match is None:
			self.match = int(match_id)
		else:
			raise Exception('Unexpected match data given: match->' + str(match) + ', match_id->' + str(match_id))

		self.map_num = int(map_num)

		# The ID of the map played
		self.ow_map_id = ow_map_id

		# The match length in minutes. If the value from the API is invalid, it is None.
		self.total_game_time = total_game_time

		# Indexed by player_id
		if t1_player_stats is None:
			self.t1_player_stats = dict()
		elif type(t1_player_stats) is dict:
			self.t1_player_stats = t1_player_stats
		elif type(t1_player_stats) in [list, str]:
			if type(t1_player_stats) is str:
				t1_player_stats = t1_player_stats.split(',')
			self.t1_player_stats = {int(v):None for v in t1_player_stats}
		else:
			raise Exception('Unexpected t1_player_stats data given: t1_player_stats->' + str(t1_player_stats))
		
		if t2_player_stats is None:
			self.t2_player_stats = dict()
		elif type(t2_player_stats) is dict:
			self.t2_player_stats = t2_player_stats
		elif type(t2_player_stats) in [list, str]:
			if type(t2_player_stats) is str:
				t2_player_stats = t2_player_stats.split(',')
			self.t2_player_stats = {int(v):None for v in t2_player_stats}
		else:
			raise Exception('Unexpected t2_player_stats data given: t2_player_stats->' + str(t2_player_stats))

	def getID(self):
		if type(self.match) is Match:
			return (self.match.id_num, self.map_num)
		elif type(self.match) is int:
			return (self.match, self.map_num)
		else:
			raise Exception('Invalid match value: ' + str(self.match))

	def getFullString(self, separator, equal_symbol):
		values = [('match_id', self.match.id_num), ('map_num', self.map_num), ('ow_map_id', self.ow_map_id),
					('total_game_time', self.total_game_time),
					('t1_player_stats', listToString(self.t1_player_stats.keys())), ('t2_player_stats', listToString(self.t2_player_stats.keys()))]

		return separator.join(map(lambda x: str(x[0]) + equal_symbol + str(x[1]), values))

class PlayerStats(object):
	def __init__(self, player = None, player_id = None, map_stats = None, match_id = None, map_num = None, hero_stats = None):
		if type(player) is Player and player_id is None:
			self.player = player
		elif type(player_id) in [int, str] and player is None:
			self.player = int(player_id)
		else:
			raise Exception('Unexpected player data given: player->' + str(player) + ', player_id->' + str(player_id))
		
		if type(map_stats) is MapStats and match_id is None and map_num is None:
			self.map_stats = map_stats
		elif (type(match_id), type(map_num)) in [(int, int), (str, str)] and map_stats is None:
			self.map_stats = (int(match_id), int(map_num))
		else:
			raise Exception('Unexpected map_stats data given: map_stats->' + str(map_stats) + ', (match_id, map_num)->(' + str(match_id) + ', ' + str(map_num) + ')')

		# Indexed by hero_id
		if hero_stats is None:
			self.hero_stats = dict()
		elif type(hero_stats) is dict:
			self.hero_stats = hero_stats
		elif type(hero_stats) in [list, str]:
			if type(hero_stats) is str:
				hero_stats = hero_stats.split(',')
			self.hero_stats = {v:None for v in hero_stats}
		else:
			raise Exception('Unexpected hero_stats data given: hero_stats->' + str(hero_stats))

	def getID(self):
		if type(self.map_stats) is MapStats:
			match_id, map_num = self.map_stats.getID()
		elif type(self.map_stats) is tuple:
			match_id, map_num = self.map_stats
		else:
			raise Exception('Invalid map_stats value: ' + str(self.map_stats))

		if type(self.player) is Player:
			player_id = self.player.id_num
		elif type(self.player) is int:
			player_id = self.player
		else:
			raise Exception('Invalid player value: ' + str(self.player))

		return (match_id, map_num, player_id)

	def getFullString(self, separator, equal_symbol):
		values = [('match_id', self.map_stats.match.id_num), ('map_num', self.map_stats.map_num), ('player_id', self.player.id_num),
					('hero_stats', listToString(self.hero_stats.keys()))]

		return separator.join(map(lambda x: str(x[0]) + equal_symbol + str(x[1]), values))

class HeroStats(object):
	def __init__(self, player_stats = None, match_id = None, map_num = None, player_id = None,
					hero = None, eliminations = 0, deaths = 0, damage = 0.0, healing = 0.0):
		if type(player_stats) is PlayerStats and match_id is None and map_num is None and player_id is None:
			self.player_stats = player_stats
		elif (type(match_id), type(map_num), type(player_id)) in [(int, int, int), (str, str, str)] and player_stats is None:
			self.player_stats = (int(match_id), int(map_num), int(player_id))
		else:
			raise Exception('Unexpected player_stats data given: player_stats->' + str(player_stats) + ', (match_id, map_num, player_id)->(' + str(match_id) + ', ' + str(map_num) + ', ' + str(player_id) + ')')

		if hero is None:
			raise Exception('Invalid hero value: ' + str(hero))
		else:
			self.hero = hero

		# These are the only stats available through the API
		self.eliminations = int(eliminations)
		self.deaths       = int(deaths)
		self.damage       = float(damage)
		self.healing      = float(healing)

	def getID(self):
		if type(self.player_stats) is PlayerStats:
			match_id, map_num, player_id = self.player_stats.getID()
		elif type(self.player_stats) is tuple:
			match_id, map_num, player_id = self.player_stats
		else:
			raise Exception('Invalid player_stats value: ' + str(self.player_stats))

		return (match_id, map_num, player_id, self.hero)

	def getFullString(self, separator, equal_symbol):
		values = [('match_id', self.player_stats.map_stats.match.id_num), ('map_num', self.player_stats.map_stats.map_num), ('player_id', self.player_stats.player.id_num),
					('hero', self.hero), ('eliminations', self.eliminations), ('deaths', self.deaths), ('damage', self.damage), ('healing', self.healing)]

		return separator.join(map(lambda x: str(x[0]) + equal_symbol + str(x[1]), values))
