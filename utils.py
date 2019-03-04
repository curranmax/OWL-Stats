
from constants import *
from data_classes import *

import json
import urllib2
import time
import os.path

from collections import defaultdict

# --------------------------------------
# |     High Level Data Management     |
# --------------------------------------

def constructInitialDatabase():
	# TODO make this function get ALL needed data including matches and stuff
	data = getAllDataFromAPI()

	checkAllData(data)

	writeDataToFiles(data)

# -------------------
# |     OWL API     |
# -------------------

def getJSONFromURL(url):
	try:
		return json.load(urllib2.urlopen(url))
	except urllib2.HTTPError:
		return None

def convertUnicodeStringToRegularString(u_str):
	return u_str.encode('ascii', 'replace')

def getAllDataFromAPI():
	vals = getJSONFromURL(teams_url)
	if vals == None:
		raise Exception('Unable to get OWL Teams url')

	print 'Parsing OWL Divisions'
	# Divisions, indexed by division's id
	divisions = dict()
	for div_json in vals['owl_divisions']:
		name   = div_json['name']
		id_num = int(div_json['id'])
		abbrev = div_json['abbrev']

		name, abbrev = map(convertUnicodeStringToRegularString, (name, abbrev))

		div = Division(name, id_num, abbrev)
		divisions[div.id_num] = div

	if len(divisions) != 2:
		raise Exception('Unexpected number of divisions: ' + len(divisions))

	print 'Parsing OWL Teams'
	# Teams indexed by team's id
	teams = dict()
	for team_json in vals['competitors']:
		team_json = team_json['competitor']

		name     = team_json['name']
		id_num   = int(team_json['id'])
		abbrev   = team_json['abbreviatedName']
		location = team_json['homeLocation']

		logo_url = team_json['logo']
		icon_url = team_json['icon']
		primary_color = team_json['primaryColor']
		secondary_color = team_json['secondaryColor']

		div_id = int(team_json['owl_division'])
		if div_id not in divisions:
			raise Exception('Unexpected division id: ' + str(div_id))

		name, abbrev, location, logo_url, icon_url, primary_color, secondary_color = \
				map(convertUnicodeStringToRegularString, (name, abbrev, location, logo_url, icon_url, primary_color, secondary_color))

		div = divisions[div_id]

		team = Team(name, id_num)
		team.division = div
		team.addFullData(abbrev, location, logo_url, icon_url, primary_color, secondary_color)
		teams[team.id_num] = team

		div.teams[team.id_num] = team

	if len(teams) != 20:
		raise Exception('Unexpected number of teams: ' + len(teams))

	vals = getJSONFromURL(players_url)
	if vals == None:
		raise Exception('Unable to get OWL Player url')

	print 'Parsing OWL Players'
	# Players indexed by player's id
	players = dict()
	for player_json in vals['content']:
		name   = player_json['name']
		id_num = int(player_json['id'])

		role   = player_json['attributes']['role']
		number = int(player_json['attributes']['player_number'])
		if 'heroes' in player_json['attributes']:
			heroes = player_json['attributes']['heroes']
		else:
			heroes = []


		given_name  = player_json['givenName']
		family_name = player_json['familyName']

		headshot_url = player_json['headshot']

		if 'homeLocation' in player_json:
			home_location = player_json['homeLocation']
		else:
			home_location = ''

		if 'nationality' in player_json:
			nationality = player_json['nationality']
		else:
			nationality = ''

		# player_json['accounts'] is the players social media accounts

		if len(player_json['teams']) != 1:
			raise Exception('Assumed each player was only associated with current team')

		team_id = int(player_json['teams'][0]['team']['id'])
		team = teams[team_id]

		name, role, given_name, family_name, headshot_url, home_location, nationality = \
				map(convertUnicodeStringToRegularString, (name, role, given_name, family_name, headshot_url, home_location, nationality))
		heroes = map(convertUnicodeStringToRegularString, heroes)

		player = Player(name, id_num)
		player.team = team
		player.addFullData(role, heroes, number, given_name, family_name, home_location, nationality, headshot_url)
		players[player.id_num] = player

		team.current_players[player.id_num] = player

	# schedule
	vals = getJSONFromURL(schedule_url)
	if vals == None:
		raise Exception('Unable to get OWL Schedule url')

	print 'Parsing OWL Schedule'
	# Matches indexed by match_id
	matches = dict()
	season_id = int(vals['data']['id'])
	for stage_json in vals['data']['stages']:
		stage_num  = int(stage_json['id']) + 1

		if stage_json['name'] != 'Stage ' + str(stage_num):
			raise Exception('Unexpected stage name/num: ' + str(stage_json['name']) + ', ' + str(stage_num))

		for week_json in stage_json['weeks']:
			week_num = int(week_json['id']) + 1

			if week_json['name'] != 'Week ' + str(week_num):
				raise Exception('Unexpected week name/num: ' + str(week_json['name']) + ', ' + str(week_num))

			for match_json in week_json['matches']:
				match_id = int(match_json['id'])

				if len(match_json['competitors']) != 2:
					raise Exception('Unexpected number of competitors: ' + str(len(match_json['competitors'])))

				team1_id = int(match_json['competitors'][0]['id'])
				team2_id = int(match_json['competitors'][1]['id'])

				team1 = teams[team1_id]
				team2 = teams[team2_id]

				scheduled_start = time.localtime(float(match_json['startDateTS']) / 1000.0)

				match = Match(team1, team2, match_id, stage_num, week_num, scheduled_start)

				team1.matches[match.id_num] = match
				team2.matches[match.id_num] = match

				match_status = matchStatusFromString(match_json['status'])

				if match_status == MatchStatus.CONCLUDED:
					# Get result
					t1_score, t2_score = map(lambda x: MatchScore(*map(int, x)), (v for v in zip(match_json['wins'], match_json['ties'], match_json['losses'])))

					actual_start = time.localtime(float(match_json['actualStartDate']) / 1000.0)
					actual_end   = time.localtime(float(match_json['actualEndDate']) / 1000.0)

					match.addConcludedData(t1_score, t2_score, actual_start, actual_end)

				elif match_status == MatchStatus.IN_PROGRESS:
					match.addInProgressData()
				elif match_status == MatchStatus.PENDING:
					match.addPendingData()
				else:
					raise Exception('Unknown MatchStatus')


				matches[match.id_num] = match

	print 'Parsing OWL Stats'
	# individual match stats
	for _, match in matches.iteritems():
		# Only get stats for finished games
		if match.match_status != MatchStatus.CONCLUDED:
			continue

		map_stat_urls = getMapStatsURLs(match.id_num)

		for map_stat_url in map_stat_urls:
			map_stat_json = getJSONFromURL(map_stat_url)
			if map_stat_json == None:
				# Can check whehter this should happen based on the match status and result.
				continue

			map_num = int(map_stat_json['game_number'])
			ow_map_id = convertUnicodeStringToRegularString(map_stat_json['map_id'])

			if len(map_stat_json['stats']) != 1 or map_stat_json['stats'][0]['name'] != 'total_game_time':
				raise Exception('Unexpected map stat: ' + str(map_stat_json['stat']))

			total_game_time = float(map_stat_json['stats'][0]['value']) / 1000.0 / 60.0
			if total_game_time <= 0.0:
				total_game_time = None

			# TODO add in the scores for this map
			map_stats = MapStats(match, map_num, ow_map_id, total_game_time)

			match.map_stats[map_stats.getID()] = map_stats

			if int(map_stat_json['teams'][0]['esports_team_id']) == match.team1.id_num and int(map_stat_json['teams'][1]['esports_team_id']) == match.team2.id_num:
				ps_order = [map_stats.t1_player_stats, map_stats.t2_player_stats]
			elif int(map_stat_json['teams'][1]['esports_team_id']) == match.team1.id_num and int(map_stat_json['teams'][0]['esports_team_id']) == match.team2.id_num:
				ps_order = [map_stats.t2_player_stats, map_stats.t1_player_stats]
			else:
				raise Exception('Unexpected team_ids: expected' + str(match.team1.id_num) + ' and ' + str(match.team2.id_num) + ', got ' + str(map_stat_json['teams'][0]['esports_team_id']) + ' and ' + str(map_stat_json['teams'][1]['esports_team_id']))

			for ms_dict, team_stat_json in zip(ps_order, map_stat_json['teams']):
				for player_stat_json in team_stat_json['players']:
					player_id = int(player_stat_json['esports_player_id'])
					if player_id not in players:
						raise Exception('Unexpected player_id: ' + str(player_id))

					player = players[player_id]

					player_stats = PlayerStats(player, map_stats)
					ms_dict[player_stats.player.id_num] = player_stats
					player.map_stats[map_stats.getID()] = player_stats

					for hero_stats_json in player_stat_json['heroes']:
						# TODO convert the hero name/id to something more concrete
						hero_str = convertUnicodeStringToRegularString(hero_stats_json['name'])
						stats = {convertUnicodeStringToRegularString(stat_json['name']): float(stat_json['value']) for stat_json in hero_stats_json['stats']}

						hero_stats = HeroStats(player_stats, hero_str, **stats)
						player_stats.hero_stats[hero_stats.hero] = hero_stats

	return AllData(divisions, teams, players, matches)

# ----------------------
# |     Local Data     |
# ----------------------

def writeDataToFiles(data,
		base_folder = default_base_folder,
		team_player_index = default_team_player_index, schedule_file = default_schedule_file,
		teams_folder = default_teams_folder, players_folder = default_players_folder, matches_folder = default_matches_folder,
		file_ext = default_file_ext,
		separator = default_separator, equal_symbol = default_equal_symbol,
		division_prefix = default_division_prefix, team_prefix = default_team_prefix, player_prefix = default_player_prefix,
		match_prefix = default_match_prefix, map_stats_prefix = default_map_stat_prefix,
		player_stats_prefix = default_player_stats_prefix, hero_stats_prefix = default_hero_stats_prefix):
	# TODO create the required folders if they do not exist

	# High level info on divisions, teams, and players
	tp_ind_f = open(os.path.join(base_folder, team_player_index), 'w')

	for _, division in data.divisions.iteritems():
		tp_ind_f.write(division_prefix + separator + division.getFullString(separator = separator, equal_symbol = equal_symbol) + '\n')

	for _, team in data.teams.iteritems():
		tp_ind_f.write(team_prefix + separator + team.getEssentialString(separator = separator, equal_symbol = equal_symbol) + '\n')

	for _, player in data.players.iteritems():
		tp_ind_f.write(player_prefix + separator + player.getEssentialString(separator = separator, equal_symbol = equal_symbol) + '\n')

	tp_ind_f.close()

	sched_f = open(os.path.join(base_folder, schedule_file), 'w')

	for _, match in data.matches.iteritems():
		sched_f.write(match_prefix + separator + match.getEssentialString(separator = separator, equal_symbol = equal_symbol) + '\n')

	sched_f.close()

	# Full team files
	for _, team in data.teams.iteritems():
		this_team_f = open(os.path.join(base_folder, teams_folder, str(team.id_num) + file_ext), 'w')

		this_team_f.write(team.getFullString(separator = '\n', equal_symbol = equal_symbol))

		this_team_f.close()

	# Full player files
	for _, player in data.players.iteritems():
		this_player_f = open(os.path.join(base_folder, players_folder, str(player.id_num) + file_ext), 'w')

		this_player_f.write(player.getFullString(separator = '\n', equal_symbol = equal_symbol))

		this_player_f.close()

	# Matches with match data
	for _, match in data.matches.iteritems():
		this_match_f = open(os.path.join(base_folder, matches_folder, str(match.id_num) + file_ext), 'w')

		this_match_f.write(match_prefix + separator + match.getFullString(separator = separator, equal_symbol = equal_symbol) + '\n')

		for _, map_stats in match.map_stats.iteritems():
			this_match_f.write(map_stats_prefix + separator + map_stats.getFullString(separator = separator, equal_symbol = equal_symbol) + '\n')

			for team_player_stats in [map_stats.t1_player_stats, map_stats.t2_player_stats]:
				for _, player_stats in team_player_stats.iteritems():
					this_match_f.write(player_stats_prefix + separator + player_stats.getFullString(separator = separator, equal_symbol = equal_symbol) + '\n')

					for _, hero_stats in player_stats.hero_stats.iteritems():
						this_match_f.write(hero_stats_prefix + separator + hero_stats.getFullString(separator = separator, equal_symbol = equal_symbol) + '\n')
# -----------------------
# |     Print Utils     |
# -----------------------
def printDivisions(divisions, sort = True):
	if type(divisions) is dict:
		divisions = [d for _, d in divisions.iteritems()]

	if sort:
		divisions = sorted(divisions, key = lambda x: x.name)

	for d in divisions:
		print d

		teams = [t for _, t in d.teams.iteritems()]

		for team in sorted(teams, key = lambda x: x.name):
			print '    ' + str(team)

def printTeams(teams, sort = True):
	if type(teams) is dict:
		teams = [t for _, t in teams.iteritems()]

	if sort:
		teams = sorted(teams, key = lambda x: x.name)

	for team in teams:
		print team

		players_by_role = defaultdict(list)
		for _, player in team.current_players.iteritems():
			players_by_role[player.role].append(player)

		for role, players in players_by_role.iteritems():
			if role == Role.DPS:
				print '  DPS'
			elif role == Role.TANK:
				print '  Tank'
			elif role == Role.SUPPORT:
				print '  Support'
			else:
				raise Exception('Invalid role: ' + str(role))

			for player in players:
				print '    ' + str(player)

# ----------------------
# |     Check Data     |
# ----------------------

# Check the data for consistency
def checkAllData(data):
	# Divisions
	# Teams
	# Players
	# Matches

	pass

if __name__ == '__main__':
	constructInitialDatabase()
