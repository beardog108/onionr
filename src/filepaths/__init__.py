from utils import identifyhome
import os
home = identifyhome.identify_home()
if not home.endswith('/'): home += '/'

app_root = os.path.dirname(os.path.realpath(__file__)) + '/../../'
usage_file = home + 'disk-usage.txt'
block_data_location = home + 'blocks/'

private_API_host_file = home + 'private-host.txt'

cached_storage = home + 'cachedstorage.dat'
announce_cache = home + 'announcecache.dat'
upload_list = home + 'upload-list.json'
config_file = home + 'config.json'
daemon_mark_file = home + '/daemon-true.txt'
lock_file = home + 'onionr.lock'

main_safedb = home + "main.safe.db"

data_nonce_file = home + 'block-nonces.dat'

onboarding_mark_file = home + 'onboarding-completed'

log_file = home + 'onionr.log'

restarting_indicator = home + "is-restarting"

secure_erase_key_file = home + "erase-key"

master_db_location = home + "database/"
