from onionrutils import localcommand
def check_ui(test_manager):
    endpoints = ['/']
    for point in endpoints:
        result = localcommand.local_command(point)
        if not result: raise ValueError
        result = result.lower()
        if 'script' not in result:
            print(point)
            raise ValueError(f'uicheck failed on {point}')
