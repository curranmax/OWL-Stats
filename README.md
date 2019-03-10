# Basics
First download the data from the OWL API by running:

	python data_management.py -full

This will download all data from the OWL API and save it to your local disk. For now to update to the latest data, you must re-download all of the data and wipe your old data.

You can then get the data from by doing the following:
	
	import data_management as dm

	all_data = dm.getDataFromFiles()

The data is structured as follows:

	# dict of OWL Divisions
	all_data.divisions

	# dict of OWL Teams
	all_data.teams

	# dict of OWL Players
	all_data.players

	# dict of OWL Matches
	all_data.matches


# TODO
I'm planning the following features:
- Basic stats
- Minimal update
- Manual annotation. This will allow for adding main-tank/off-tank roles.
- Better error handling