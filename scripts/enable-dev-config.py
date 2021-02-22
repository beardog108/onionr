#!/usr/bin/env python3

"""Enable dev default config"""

import json

input("enter to continue")  # hack to avoid vscode term input

conf = json.load(open('static-data/default_config.json', 'r'))

conf['general']['security_level'] = int(input("Security level:"))

conf['general']['dev_mode'] = True
conf['general']['random_bind_ip'] = False
conf['onboarding']['done'] = True

conf['log']['file']['remove_on_exit'] = False
conf['ui']['animated_background'] = False
conf['runtests']['skip_slow'] = True


json.dump(conf, open('static-data/default_config.json', 'w'), sort_keys=True, indent=4)

