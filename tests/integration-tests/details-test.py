import sys
import os
from subprocess import Popen, PIPE
import uuid

TEST_DIR = 'testdata/%s-%s' % (uuid.uuid4(), os.path.basename(__file__)) + '/'
os.environ["ONIONR_HOME"] = TEST_DIR

print(f'running integration test for {__file__}')

with Popen(['./onionr.sh', 'details'], stdout=PIPE) as onionr_proc:
    output = onionr_proc.stdout.read().decode()
if onionr_proc.returncode != 0:
    raise ValueError('Raised non zero exit ' + str(onionr_proc.returncode))

