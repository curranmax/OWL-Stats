
# File Structure
default_base_folder = 'data'

default_team_player_index = 'tp_index.txt'
default_schedule_file = 'schedule.txt'

default_teams_folder   = 'teams'
default_players_folder = 'players'
default_matches_folder = 'matches'

default_file_ext = '.txt'

# File format
default_division_prefix = 'DIV'
default_team_prefix     = 'TEAM'
default_player_prefix   = 'PLAYER'

default_match_prefix        = 'MATCH'
default_map_stat_prefix     = 'MS'
default_player_stats_prefix = 'PS'
default_hero_stats_prefix   = 'HS'

default_separator    = '\t'
default_equal_symbol = '='

# API URLS
teams_url    = 'https://api.overwatchleague.com/teams'
players_url  = 'https://api.overwatchleague.com/players'
schedule_url = 'https://api.overwatchleague.com/schedule'
maps_url     = 'https://api.overwatchleague.com/maps'

def getMapStatsURLs(match_id):
	return ['https://api.overwatchleague.com/stats/matches/' + str(match_id) + '/maps/' + str(map_num) for map_num in [1, 2, 3, 4, 5]]

