import os
from parser import ConfigFile

# determine working directory
if 'win' in os.name:
	conf_directory = os.getenv('APPDATA') + os.sep + 'HumbleAutomaton' + os.sep
	var_directory = os.getenv('APPDATA') + os.sep + 'HumbleAutomaton' + os.sep
else:
	conf_directory = '/opt/HumbleAutomaton/'
	var_directory = '/var/opt/HumbleAutomaton/'
