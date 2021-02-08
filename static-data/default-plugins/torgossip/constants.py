from utils.identifyhome import identify_home
home = identify_home()
SERVER_SOCKET = home + "torgossip.sock"
HOSTNAME_FILE = home + "torgossip-hostname"
CONFIG_FILE = home + "torgossip_config.json"
GOSSIP_PORT = 2021
