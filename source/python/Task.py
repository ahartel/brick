
class Task:

    # init
    def __init__(self,brick,sectionName,options):
        self.__name = sectionName
        self.__options = options
        self.__tool = [val for (opt,val) in options if opt=='tool'][0]

        self.__inputs,self.__outputs,self.__wscript_code = brick.run_prepare_hook(self.__tool,sectionName,options)
    # end of init

    def show_wscript(self):
        return self.__wscript_code

