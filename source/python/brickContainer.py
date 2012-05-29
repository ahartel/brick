import os

class brickContainer:

    # init
    def __init__(self,configFile,configObj):
        self.__config_file = configFile
        self.config = configObj
        self.__preRunHooks = []
        self.__state = 'initialized'
    # end of init

    def add_pre_run_hook(self,f):
        self.__preRunHooks.append(f)
    # end of add_pre_run_hook

    def print_pre_run_hooks(self):
        for func in self.__preRunHooks:
            print func.__name__
    # end of print_pre_run_hooks

    def run_pre_hooks(self):
        logger.info("Running pre_run_hooks")
        for func in self.__preRunHooks:
            logger.debug("Running pre_run_hook "+func.__name__)
            state = func(self)
            if not state:
                logger.error(" Hook returned "+str(state))
                return False
            else:
                logger.debug(" Hook returned successfully")

        return True
    # end of run_pre_hooks

    def prepare_tasks(self):
        # do something
        self.__state = 'prepared'

    def run_tasks(self):
        # do something
        self.__state = 'run'

    def postprocess_tasks(self):
        # do something
        self.__state = 'postprocessed'

    def get_full_rundir(self):
        rundir = self.config.get('global','rundir')
        if os.path.isabs(rundir):
            return rundir
        else:
            if os.path.isabs(os.path.dirname(self.__config_file)):
                return os.path.join(os.path.dirname(self.__config_file),rundir)
            else:
                return os.path.join(os.getcwd(),os.path.dirname(self.__config_file),rundir)


    def __load_config(self):
        xmlconfig = minidom.parse('./brick_config.xml') # parse an XML file by name
        self.config['projectname'] = brick_waf.getTextNodeValue(xmlconfig,'projectShortName')
        self.config['testcases'] = brick_waf.getTestCases(xmlconfig)

    def get_config_value(self,key):
        return self.config[key]


    # save state to file
    def __save_state(self):
        f = open('./.brick_info','w')
        f.write(self.__rundir+"\n")
        f.write(self.__mode+"\n")
        f.write(self.__testcase+"\n")
        f.write(self.__simulator+"\n")
        f.close()
    # end save state

    # load state from file
    def __load_state(self):
        f = open('./.brick_info','r')
        self.__rundir = f.readline().rstrip()
        self.__mode = f.readline().rstrip()
        self.__testcase = f.readline().rstrip()
        self.__simulator = f.readline().rstrip()
        f.close()
    # end save state

    # configure
    def configure(self,mode,rundir,testcase,simulator):
        # save variables in object fields and give them default values
        # rundir
        if not rundir:
            if not self.__rundir:
                self.output.append('No rundir was explecitly given. Setting rundir to current datetime string')
                import datetime
                jetzt = datetime.datetime.now()
                self.__rundir=jetzt.strftime("%Y%m%d%H%M")
        else:
            self.__rundir = rundir
        # mode
        if not mode:
            if not self.__mode:
                self.output.append('Please give a mode via the --mode option. Mode can be "build" or "functional"')
                return
        else:
            self.__mode = mode
        # testcase
        if testcase:
            self.__testcase = testcase

        if self.__mode == 'functional' and not self.__testcase:
            self.output.append("Testcase has to be given in mode 'functional'")
            return
        # simulator
        if not simulator:
            self.__simulator = 'cadence'
        else:
            self.__simulator = simulator

        cmd = ''
        if self.__mode == 'functional':
            cmd = './waf configure --mode '+self.__mode+' --out rundirs/'+self.__rundir+" --testcase "+self.__testcase+" --simulator "+self.__simulator
        else:
            cmd = './waf configure --mode '+self.__mode+' --out rundirs/'+self.__rundir

        p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
        for line in p.stdout:
            self.output.append(line.rstrip())

        self.__save_state()

        return
    # end of configure

    # build
    def build(self):
        cmd = './waf build'
        p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
        for line in p.stdout:
            self.output.append(line.rstrip())
        return
    # end of build

    # run
    def run(self):
        cmd = './waf run'
        p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
        for line in p.stdout:
            self.output.append(line.rstrip())
        return
    # end of run

    def flushOutput(self):
        returnOutput = "\n".join(self.output)
        self.output = []
        return returnOutput

