from time import sleep
from secrets import token_hex

import blockio
import logger
from onionrutils.localcommand import local_command
from blockio import list_all_blocks


def test_vdf_create_and_store(testmanager):
    # data, data_type, ttl, **metadata
    db = testmanager._too_many.get_by_string('SafeDB')
    bls = list_all_blocks(db)
    b_data = "test" + token_hex(5)
    res = local_command(
        '/serialized/SubProcVDFGenerator.gen_and_store_vdf_block', post=True, post_data={"args": [b_data, "txt", 6000]}, is_json=True)

    print(res)

    while len(list_all_blocks(db)) == len(bls):
        sleep(1)
    for i in list_all_blocks(db):
        i = bytes(i)
        b = blockio.load_block(i, db).data.decode('utf-8')

        if b == b_data:
            break
    else:
        logger.error("Block was not generated", terminal=True)
        raise ValueError

