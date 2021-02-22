from blockio import subprocgenerate


class SubProcVDFGenerator:
    def __init__(self, shared_state):
        self.shared_state = shared_state

    def gen_and_store_vdf_block(self, *args, **kwargs):

        return subprocgenerate.gen_and_store_vdf_block(
            self.shared_state, *args, **kwargs)
