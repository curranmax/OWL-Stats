
import enum

class AllData:
	def __init__(self, divisions, teams, players, matches):
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

class Division:
	def __init__(self, name, id_num, abbrev):
		self.scale = Scale.FULL
		
		# Essential Data
		self.name   = name
		self.id_num = int(id_num)
		self.abbrev = abbrev

		# Links to other data
		self.teams = dict()

	def getFullString(self, separator, equal_symbol):
		if self.scale != Scale.FULL:
			raise Exception('Cannot get full string for non-full division')

		values = [('name', self.name), ('id_num', self.id_num), ('abbrev', self.abbrev), ('team_ids', listToString(self.teams.keys()))]

		return separator.join(map(lambda x: str(x[0]) + equal_symbol + str(x[1]), values))

	def __str__(self):
		return self.name + ' (' + self.abbrev + ')'

class Team:
	def __init__(self, name, id_num):
		self.scale = Scale.ESSENTIAL

		# Essential Data
		self.name     = name
		self.id_num   = int(id_num)

		# Links to other data.
		self.division = None
		self.current_players = dict()
		self.matches = dict()

		# Other Data
		self.abbrev   = None
		self.location = None

		self.logo_url        = None
		self.icon_url        = None
		self.primary_color   = None
		self.secondary_color = None

	def addFullData(self, abbrev, location, logo_url, icon_url, primary_color, secondary_color):
		self.scale = Scale.FULL

		self.abbrev   = abbrev
		self.location = location

		self.logo_url        = logo_url
		self.icon_url        = icon_url
		self.primary_color   = primary_color
		self.secondary_color = secondary_color

	def getEssentialString(self, separator, equal_symbol):
		values = [('name', self.name), ('id_num', self.id_num), ('division_id', self.division.id_num),
					('player_ids', listToString(self.current_players.keys())), ('match_ids', listToString(self.matches.keys()))]

		return separator.join(map(lambda x: str(x[0]) + equal_symbol + str(x[1]), values))

	def getFullString(self, separator, equal_symbol):
		values = [('name', self.name), ('id_num', self.id_num), ('division_id', self.division.id_num),
					('player_ids', listToString(self.current_players.keys())), ('match_ids', listToString(self.matches.keys())),
					('abbrev', self.abbrev), ('location', self.location),
					('logo_url', self.logo_url), ('icon_url', self.icon_url), ('primary_color', self.primary_color), ('secondary_color', self.secondary_color)]

		return separator.join(map(lambda x: str(x[0]) + equal_symbol + str(x[1]), values))

	def __str__(self):
		return self.name + ' (' + self.abbrev + ')'

class Player:
	def __init__(self, name, id_num):
		self.scale = Scale.ESSENTIAL

		# Essential Data
		self.name   = name
		self.id_num = int(id_num)

		# Links to other data
		self.team = None

		# Stats for this player for all maps. Indexed by (match_id, map_num). Values are PlayerStats objects.
		self.map_stats = dict()

		# Other data
		self.role   = None
		self.heroes = None
		self.number = None

		self.given_name    = None
		self.family_name   = None
		self.home_location = None
		self.nationality   = None
		self.headshot_url  = None

	def addFullData(self, role, heroes, number, given_name, family_name, home_location, nationality, headshot_url):
		self.scale = Scale.FULL

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
					('map_stat_ids', listToString(self.map_stats.keys(), separator = ';', map_func = listToString))]

		return separator.join(map(lambda x: str(x[0]) + equal_symbol + str(x[1]), values))

	def getFullString(self, separator, equal_symbol):
		values = [('name', self.name), ('id_num', self.id_num), ('team_id', self.team.id_num),
					('map_stat_ids', listToString(self.map_stats.keys(), separator = ';', map_func = listToString)),
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
	if ms_str in ['CONCLUDED']:
		return MatchStatus.CONCLUDED

	if ms_str in ['IN_PROGRESS']:
		return MatchStatus.IN_PROGRESS

	if ms_str in ['PENDING']:
		return MatchStatus.PENDING

	raise Exception('Unexpected match state string: ' + str(ms_str))

class Match:
	def __init__(self, team1, team2, id_num, stage_num, week_num, scheduled_start):
		# Essential data
		self.match_status = None

		self.team1  = team1
		self.team2  = team2
		self.id_num = id_num

		self.stage_num = stage_num
		self.week_num  = week_num

		self.t1_score = None
		self.t2_score = None

		# Other data
		self.scheduled_start = scheduled_start

		self.actual_start = None
		self.actual_end   = None

		self.map_stats = dict()

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
		values = [('match_status', self.match_status), ('id_num', self.id_num), ('team1_id', self.team1.id_num), ('team2_id', self.team1.id_num),
					('stage_num', self.stage_num), ('week_num', self.week_num),
					('map_stat_ids', listToString(self.map_stats.keys(), separator = ';', map_func = listToString))]

		if self.match_status == MatchStatus.CONCLUDED:
			values += [('t1_score', self.t1_score), ('t2_score', self.t2_score)]

		return separator.join(map(lambda x: str(x[0]) + equal_symbol + str(x[1]), values))

	def getFullString(self, separator, equal_symbol):
		# TODO output the times in a good way
		values = [('match_status', self.match_status), ('id_num', self.id_num), ('team1_id', self.team1.id_num), ('team2_id', self.team1.id_num),
					('stage_num', self.stage_num), ('week_num', self.week_num), ('scheduled_start', self.scheduled_start),
					('map_stat_ids', listToString(self.map_stats.keys(), separator = ';', map_func = listToString))]

		if self.match_status == MatchStatus.CONCLUDED:
			values += [('t1_score', self.t1_score), ('t2_score', self.t2_score),
						('actual_start', self.actual_start), ('actual_end', self.actual_end)]

		return separator.join(map(lambda x: str(x[0]) + equal_symbol + str(x[1]), values))

	def __str__(self):
		str_val = 'Stage ' + str(stage_num) + ', Week ' + str(week_num) + ', ' + str(self.team1) + ' vs. ' + str(self.team2)

		if self.match_status == MatchStatus.CONCLUDED:
			str_val += ' (' + str(self.t1_score.wins) + '-' + str(self.t2_score) + ')'
		return str_val

class MatchScore:
	def __init__(self, wins, ties, losses):
		self.wins   = wins
		self.ties   = ties
		self.losses = losses

	def __str__(self):
		return 'W:' + str(self.wins) + '-T:' + str(self.ties) + '-L:' + str(self.losses)

class MapStats:
	def __init__(self, match, map_num, ow_map_id, total_game_time):
		# Link to the match this map was from
		self.match = match

		self.map_num = map_num

		# The ID of the map played
		self.ow_map_id = ow_map_id

		# The match length in minutes. If the value from the API is invalid, it is None.
		self.total_game_time = total_game_time

		# Indexed by player_id
		self.t1_player_stats = dict()
		self.t2_player_stats = dict()

	def getID(self):
		return (self.match.id_num, self.map_num)

	def getFullString(self, separator, equal_symbol):
		values = [('match_id', self.match.id_num), ('map_num', self.map_num), ('ow_map_id', self.ow_map_id),
					('total_game_time', self.total_game_time),
					('t1_player_stats', listToString(self.t1_player_stats.keys())), ('t2_player_stats', listToString(self.t2_player_stats.keys()))]

		return separator.join(map(lambda x: str(x[0]) + equal_symbol + str(x[1]), values))

class PlayerStats:
	def __init__(self, player, map_stats):
		self.player    = player
		self.map_stats = map_stats

		# Indexed by hero_id
		self.hero_stats = dict()

	def getFullString(self, separator, equal_symbol):
		values = [('match_id', self.map_stats.match.id_num), ('map_num', self.map_stats.map_num), ('player_id', self.player.id_num),
					('hero_stats', listToString(self.hero_stats.keys()))]

		return separator.join(map(lambda x: str(x[0]) + equal_symbol + str(x[1]), values))

class HeroStats:
	def __init__(self, player_stat, hero, eliminations = 0.0, deaths = 0.0, damage = 0.0, healing = 0.0):
		self.player_stats = player_stat

		self.hero = hero

		# These are the only stats available through the API
		self.eliminations = eliminations
		self.deaths       = deaths
		self.damage       = damage
		self.healing      = healing

	def getFullString(self, separator, equal_symbol):
		values = [('match_id', self.player_stats.map_stats.match.id_num), ('map_num', self.player_stats.map_stats.map_num), ('player_id', self.player_stats.player.id_num),
					('hero', self.hero), ('eliminations', self.eliminations), ('deaths', self.deaths), ('damage', self.damage), ('healing', self.healing)]

		return separator.join(map(lambda x: str(x[0]) + equal_symbol + str(x[1]), values))
