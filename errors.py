import logging

class DialFailed(Exception):
	pass

# We'll use this boolean variable wherever we
# need to print out debugging output.
debugging = False

# Should we log to a file?
loggingToFile = False

# Default for normal operation
debugLevel=1

logger = logging.getLogger("")
logger.setLevel(debugLevel)

logFormat = logging.Formatter('%(asctime)s::%(levelname)s::[%(module)s:%(lineno)d] %(message)s')

# create a log handler to stdout
console = logging.StreamHandler()
console.setFormatter(logFormat)
logger.addHandler(console)
