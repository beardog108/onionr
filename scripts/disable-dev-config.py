#!/usr/bin/env python3

"""Enable dev default config"""

import json

conf = json.load(open('static-data/default_config.json', 'r'))


conf['general']['dev_mode'] = False
conf['general']['display_header'] = True
conf['general']['security_level'] = 0
conf['onboarding']['done'] = False
conf['log']['file']['remove_on_exit'] = True
conf['ui']['animated_background'] = True
conf['runtests']['skip_slow'] = False

json.dump(conf, open('static-data/default_config.json', 'w'), sort_keys=True, indent=4)

