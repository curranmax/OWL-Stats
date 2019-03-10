
import data_management as dm
import data_classes as dc

import argparse
from collections import defaultdict

# Returns a list of PlayerStats for the given Player and given qualifiers.
# Qualifiers:
#	matches -> List of desired matches. (Either list of Match objects or match_ids)
#	stage_num -> Desired stage by its number. (For now can only be one value. TODO support multiple stages)
#	week_num -> Desired week in a stage by its number. Must also supply a stage_num. (TODO support multiple weeks)
# TODO add more qualifiers (such as opponent)
def getPlayerStats(player, matches = None, stage_num = None, week_num = None):
	# If matches is a single match (or match_id) it is wrapped in a list.
	if type(matches) in [dc.Match, int]:
		matches = [matches]

	if type(matches) is list:
		# If matches is a list, then all entries that are Match objects are replaced by the object's id_num. (TODO assume other entries are id_nums)
		matches = [(v.id_num if type(v) is dc.Match else v) for v in matches]
	elif matches is not None:
		raise Exception('Unexpected matches value: ' + str(matches))

	if week_num is not None and stage_num is None:
		raise Exception('Must supply stage_num, if supplying non-None week_num')

	player_stats = []
	for _, ps in player.player_stats.iteritems():
		match_check = (matches is None   or ps.map_stats.match.id_num in matches)
		stage_check = (stage_num is None or ps.map_stats.match.stage_num is stage_num)
		week_check  = (week_num is None  or ps.map_stats.match.week_num is week_num)

		if all((match_check, stage_check, week_check)):
			player_stats.append(ps)

	return player_stats

# Calculate the fantasy points using Highnoon.gg's formula.
def highnoonFantasyFunc(player_stats):
	total_points = 0.0
	for ps in player_stats:
		for _, hs in ps.hero_stats.iteritems():
			total_points += hs.eliminations / 2.0
			total_points += hs.damage / 1000.0
			total_points += hs.healing / 1000.0

	return total_points

# Calculates the fantasy points for a given player grouped by match.
# Qualifiers are same as getPlayerStats
# fantasy_points_func must be a function that takes a list of PlayerStats and returns the fantasy points from that list
def getFantasyPoints(player, matches = None, stage_num = None, week_num = None, fantasy_points_func = highnoonFantasyFunc):
	# Get the player_stats
	player_stats = getPlayerStats(player, matches = matches, stage_num = stage_num, week_num = week_num)

	# Group by match
	ps_by_match = defaultdict(list)

	for ps in player_stats:
		ps_by_match[ps.map_stats.match.id_num].append(ps)

	fantasy_points_by_match = {match_id:fantasy_points_func(pss) for match_id, pss in ps_by_match.iteritems()}

	return fantasy_points_by_match

# Nicely displays the fantasy points earned for a given player
# fp_data is a list of 2-tuple (Match, fantasy points earned in that match)
def printFantasyPoints(player, fp_data):
	print 'Fantasy points for', player.name, 'from', player.team

	data_by_stage_and_week = defaultdict(lambda:defaultdict(list))
	for match, fp in fp_data:
		data_by_stage_and_week[match.stage_num][match.week_num].append((match, fp))

	for stage_num in sorted(data_by_stage_and_week):
		data_by_week = data_by_stage_and_week[stage_num]

		if len(data_by_stage_and_week) > 1:
			print 'Stage', stage_num
			week_prefix = ' ' * 5
		else:
			week_prefix = ''

		for week_num in sorted(data_by_week):
			if len(data_by_stage_and_week) > 1 or len(data_by_week) > 1:
				print week_prefix + 'Week', week_num
				match_prefix = week_prefix + ' ' * 5
			else:
				match_prefix = week_prefix

			# TODO sort by scheduled_start so it matches the schedule
			# TODO maybe show games in which the players team played in, but they didn't play in themselves
			for match, fp in data_by_week[week_num]:
				print match_prefix + 'vs.', match.getOtherTeam(player.team).abbrev, '===>', fp

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description = 'Compute basic stats for OWL')

	parser.add_argument('-n','--player_name', metavar = 'NAME', type = str, nargs = 1, default = [''], help = 'Name of player to calculate Highnoon.gg fantasy points for.')
	
	args = parser.parse_args()

	player_name = args.player_name[0]

	all_data = dm.getDataFromFiles()

	player = all_data.getPlayer(player_name)

	if player is None:
		raise Exception('No plaer found with name: ' + str(player_name))

	fp_by_match = getFantasyPoints(player)

	printFantasyPoints(player, [(all_data.matches[match_id], fp) for match_id, fp in fp_by_match.iteritems()])
