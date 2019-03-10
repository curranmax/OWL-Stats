
from constants import *
from data_classes import *

import json
import urllib2
import time
import os.path

from collections import defaultdict

import argparse

# --------------------------------------
# |     High Level Data Management     |
# --------------------------------------

def constructDatabase():
	# TODO make this function get ALL needed data including matches and stuff
	data = getAllDataFromAPI()

	# checkAllData(data)

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

		div = Division(name = name, id_num = id_num, abbrev = abbrev)
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

		team = Team(name = name, id_num = id_num, division = div)
		team.addFullData(abbrev =abbrev, location =location, logo_url =logo_url, icon_url =icon_url, primary_color =primary_color, secondary_color =secondary_color)
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

		player = Player(name = name, id_num = id_num, team = team)
		player.addFullData(role = role, heroes = heroes, number = number, given_name = given_name, family_name = family_name, home_location = home_location, nationality = nationality, headshot_url = headshot_url)
		players[player.id_num] = player

		team.players[player.id_num] = player

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

				if match_json['competitors'][0] is None or match_json['competitors'][1] is None:
					continue
				team1_id = int(match_json['competitors'][0]['id'])
				team2_id = int(match_json['competitors'][1]['id'])

				team1 = teams[team1_id]
				team2 = teams[team2_id]

				scheduled_start = time.localtime(float(match_json['startDateTS']) / 1000.0)

				match = Match(team1 = team1, team2 =team2, id_num = match_id, stage_num = stage_num, week_num = week_num, scheduled_start = scheduled_start)

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
			map_stats = MapStats(match = match, map_num = map_num, ow_map_id = ow_map_id, total_game_time = total_game_time)

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

					player_stats = PlayerStats(player = player, map_stats = map_stats)
					ms_dict[player_stats.player.id_num] = player_stats
					player.player_stats[player_stats.getID()] = player_stats

					for hero_stats_json in player_stat_json['heroes']:
						# TODO convert the hero name/id to something more concrete
						hero_str = convertUnicodeStringToRegularString(hero_stats_json['name'])
						stats = {convertUnicodeStringToRegularString(stat_json['name']): float(stat_json['value']) for stat_json in hero_stats_json['stats']}

						hero_stats = HeroStats(player_stats = player_stats, hero = hero_str, **stats)
						player_stats.hero_stats[hero_stats.hero] = hero_stats

	return AllData(divisions = divisions,
					teams = teams,
					players = players,
					matches = matches)

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

	if not os.path.exists(base_folder):
		os.makedirs(base_folder)

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

	if not os.path.exists(os.path.join(base_folder, teams_folder)):
		os.makedirs(os.path.join(base_folder, teams_folder))

	# TODO make a easier way to modify the individual file names
	# Full team files
	for _, team in data.teams.iteritems():
		this_team_f = open(os.path.join(base_folder, teams_folder, str(team.id_num) + file_ext), 'w')

		this_team_f.write(team.getFullString(separator = '\n', equal_symbol = equal_symbol))

		this_team_f.close()

	if not os.path.exists(os.path.join(base_folder, players_folder)):
		os.makedirs(os.path.join(base_folder, players_folder))

	# Full player files
	for _, player in data.players.iteritems():
		this_player_f = open(os.path.join(base_folder, players_folder, str(player.id_num) + file_ext), 'w')

		this_player_f.write(player.getFullString(separator = '\n', equal_symbol = equal_symbol))

		this_player_f.close()

	if not os.path.exists(os.path.join(base_folder, matches_folder)):
		os.makedirs(os.path.join(base_folder, matches_folder))

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

def getDataFromFiles(
		base_folder = default_base_folder,
		team_player_index = default_team_player_index, schedule_file = default_schedule_file,
		teams_folder = default_teams_folder, players_folder = default_players_folder, matches_folder = default_matches_folder,
		file_ext = default_file_ext,
		separator = default_separator, equal_symbol = default_equal_symbol,
		division_prefix = default_division_prefix, team_prefix = default_team_prefix, player_prefix = default_player_prefix,
		match_prefix = default_match_prefix, map_stats_prefix = default_map_stat_prefix,
		player_stats_prefix = default_player_stats_prefix, hero_stats_prefix = default_hero_stats_prefix):
	
	data = AllData()
	# Team/Player index file
	tp_ind_f = open(os.path.join(base_folder, team_player_index), 'r')
	for line in tp_ind_f:
		spl = line.strip().split(separator)

		if len(spl) == 0:
			continue

		this_prefix = spl[0]
		values = dict(key_value.split(equal_symbol) for key_value in spl[1:])

		if this_prefix == division_prefix:
			division = Division(**values)
			data.divisions[division.id_num] = division
		elif this_prefix == team_prefix:
			team = Team(**values)
			data.teams[team.id_num] = team
		elif this_prefix == player_prefix:
			player = Player(**values)
			data.players[player.id_num] = player

	tp_ind_f.close()

	# Schedule file
	sched_f = open(os.path.join(base_folder, schedule_file), 'r')
	for line in sched_f:
		spl = line.strip().split(separator)

		if len(spl) == 0:
			continue

		this_prefix = spl[0]
		values = dict(key_value.split(equal_symbol) for key_value in spl[1:])

		if this_prefix == match_prefix:
			match = Match(**values)
			data.matches[match.id_num] = match

	sched_f.close()

	# Individual team files
	for _, team in data.teams.iteritems():
		this_team_f = open(os.path.join(base_folder, teams_folder, str(team.id_num) + file_ext), 'r')

		vals = []
		for line in this_team_f:
			vals.append(line.strip().split(equal_symbol))
		
		this_team_f.close()

		team.addFullData(**dict(vals))

	# Individual player files
	for _, player in data.players.iteritems():
		this_player_f = open(os.path.join(base_folder, players_folder, str(player.id_num) + file_ext), 'r')

		vals = []
		for line in this_player_f:
			vals.append(line.strip().split(equal_symbol))

		this_player_f.close()

		player.addFullData(**dict(vals))

	# Individual match files
	for _, match in data.matches.iteritems():
		this_match_f = open(os.path.join(base_folder, matches_folder, str(match.id_num) + file_ext), 'r')

		map_stats    = dict()
		player_stats = dict()
		hero_stats   = dict()

		for line in this_match_f:
			spl = line.strip().split(separator)

			if len(spl) == 0:
				continue

			prefix = spl[0]
			values = dict(key_value.split(equal_symbol) for key_value in spl[1:])
			if prefix == match_prefix:
				# Extra match data
				pass
			if prefix == map_stats_prefix:
				map_stat = MapStats(**values)
				map_stats[map_stat.getID()] = map_stat
			if prefix == player_stats_prefix:
				# Stats for a player on a map
				player_stat = PlayerStats(**values)
				player_stats[player_stat.getID()] = player_stat
			if prefix == hero_stats_prefix:
				# Stats for a player on one hero on a map
				hero_stat = HeroStats(**values)
				hero_stats[hero_stat.getID()] = hero_stat

		# Link this match to its parent teams
		if match.team1 not in data.teams:
			raise Exception('Missing team1: ' + str(match.team1))

		match.team1 = data.teams[match.team1]

		if match.team2 not in data.teams:
			raise Exception('Missing team2: ' + str(match.team2))

		match.team2 = data.teams[match.team2]
 
		# Link this matches data to its children map_stats
		for k in match.map_stats:
			if k not in map_stats:
				raise Exception('Missing map_stats: ' + str(k))
			match.map_stats[k] = map_stats[k]

		# Link the map_stat its parent match and its children player_stats
		for _, map_stat in map_stats.iteritems():
			if map_stat.match != match.id_num:
				raise Exception('Mismatching map_stat.match_id: got' + str(map_stat.match) + ', expected ' + str(match.id_num))

			map_stat.match = match

			match_id, map_num = map_stat.getID()
			for player_id in map_stat.t1_player_stats:
				if (match_id, map_num, player_id) not in player_stats:
					raise Exception('Missing player_stats: ' + str((match_id, map_num, player_id)))

				map_stat.t1_player_stats[player_id] = player_stats[(match_id, map_num, player_id)]

			for player_id in map_stat.t2_player_stats:
				if (match_id, map_num, player_id) not in player_stats:
					raise Exception('Missing player_stats: ' + str((match_id, map_num, player_id)))

				map_stat.t2_player_stats[player_id] = player_stats[(match_id, map_num, player_id)]

		# Link the player_stats to its parent map_stat and parent player, and its children hero_stats
		for _, player_stat in player_stats.iteritems():
			if player_stat.player not in data.players:
				raise Exception('Missing player: ' + str(player_stats.player))

			player_stat.player = data.players[player_stat.player]

			if player_stat.map_stats not in map_stats:
				raise Exception('Missing map_stats: ' + str(player_stats.map_stats))

			player_stat.map_stats = map_stats[player_stat.map_stats]

			match_id, map_num, player_id = player_stat.getID()
			for hero_id in player_stat.hero_stats:
				if (match_id, map_num, player_id, hero_id) not in hero_stats:
					raise Exception('Missing hero_stats: ' + str((match_id, map_num, player_id, hero_id)))

				player_stat.hero_stats[hero_id] = hero_stats[(match_id, map_num, player_id, hero_id)]

		# Link the hero_Stats to its parent player_stats
		for _, hero_stat in hero_stats.iteritems():
			if hero_stat.player_stats not in player_stats:
				raise Exception('Missing player_stats: ' + str(hero_stat.player_stats))

			hero_stat.player_stats = player_stats[hero_stat.player_stats]

	# Link each division to its children teams
	for _, division in data.divisions.iteritems():
		for team_id in division.teams:
			if team_id not in data.teams:
				raise Exception('Missing team_id: ' + str(team_id))

			division.teams[team_id] = data.teams[team_id]

	# Link each team to its parent division, and to its children matches, and children players.
	for _, team in data.teams.iteritems():
		if team.division not in data.divisions:
			raise Exception('Missing division: ' + str(team.division))

		team.division = data.divisions[team.division]

		for player_id in team.players:
			if player_id not in data.players:
				raise Exception('Missing player_id: ' + str(player_id))

			team.players[player_id] = data.players[player_id]

		for match_id in team.matches:
			if match_id not in data.matches:
				raise Exception('Missing match_id: ' + str(match_id))

			team.matches[match_id] = data.matches[match_id]

	# Link each player to its parent team, and to its children player_stats
	for _, player in data.players.iteritems():
		if player.team not in data.teams:
			raise Exception('Missing team: ' + str(player.team))

		player.team = data.teams[player.team]

		for (match_id, map_num, player_id) in player.player_stats:
			if match_id not in data.matches:
				raise Exception('Missing match_id: ' + str(match_id))

			if (match_id, map_num) not in data.matches[match_id].map_stats:
				raise Exception('Missing map_stats_id: ' + str((match_id, map_num)))

			# Check that player_id == player.id_num?
			if player_id in data.matches[match_id].map_stats[(match_id, map_num)].t1_player_stats:
				player.player_stats[(match_id, map_num, player_id)] = data.matches[match_id].map_stats[(match_id, map_num)].t1_player_stats[player_id]
			elif player_id in data.matches[match_id].map_stats[(match_id, map_num)].t2_player_stats:
				player.player_stats[(match_id, map_num, player_id)] = data.matches[match_id].map_stats[(match_id, map_num)].t2_player_stats[player_id]
			else:
				raise Exception('Missing player_id: ' + str(player_id))

	return data

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
		for _, player in team.players.iteritems():
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
	parser = argparse.ArgumentParser(description = 'Download and Update data from OWL API')

	parser.add_argument('-full','--full_download', help = 'Recreate the local database from the OWL API', action = 'store_true')
	
	args = parser.parse_args()

	if args.full_download:
		constructDatabase()
