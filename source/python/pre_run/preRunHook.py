
class preRunHook(object):
    def __init__(self,f):
        brick.add_pre_run_hook(f)
    def __call__(self,f):
        pass

