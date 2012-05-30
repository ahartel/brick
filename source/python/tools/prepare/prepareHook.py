
class prepareHook(object):
    def __init__(self,name):
        self.__name = name
    def __call__(self,f):
        brick.add_prepare_hook(self.__name,f)

