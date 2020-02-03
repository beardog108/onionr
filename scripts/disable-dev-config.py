#!/usr/bin/env python3

"""Enable dev default config"""

import json

conf = json.load(open('static-data/default_config.json', 'r'))

conf['tor']['use_existing_tor'] = False
conf['tor']['existing_control_port'] = 0
conf['tor']['existing_control_password'] = ""
conf['tor']['existing_socks_port'] = 0

conf['general']['dev_mode'] = False
conf['general']['insert_deniable_blocks'] = True
conf['general']['random_bind_ip'] = True

json.dump(conf, open('static-data/default_config.json', 'w'), sort_keys=True, indent=4)
