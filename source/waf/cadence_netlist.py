import os,re
from waflib import Task,Errors,Node,TaskGen,Configure,Logs
from brick_general import ChattyBrickTask

def configure(conf):
	conf.load('cadence_base')

	conf.env.AMSDESIGNER = 'amsdesigner'
	if not conf.env.AMSDESIGNER_OPTIONS:
		conf.env.AMSDESIGNER_OPTIONS = [
				'-rundir', '.',
				'-netlisttorundir',
				'-ncvlogopts', '-use5x -64bit'
			]

	if not conf.env.RUNAMS_OPTIONS:
		conf.env.RUNAMS_OPTIONS = []
	conf.env.RUNAMS_OPTIONS.extend(['-netlisteropts', 'amsPortConnectionByNameOrOrder=order:useSpectreInfo=spectre veriloga spice symbol'])
	conf.env.RUNAMS_OPTIONS.extend(['-solver', 'ultrasim'])
	conf.env.RUNAMS_OPTIONS.extend(['-netlist', 'all'])

	conf.find_program('runams',var='CADENCE_RUNAMS')
	conf.find_program('si', var='CADENCE_SI')

#@Task.always_run
class cdsNetlistTask(ChattyBrickTask):
	vars = ['CADENCE_RUNAMS','CDS_LIB_PATH','CDS_HDLVAR_PATH','RUNAMS_OPTIONS']
	run_str = "${env.CADENCE_RUNAMS} -lib ${gen.libname} -cell ${gen.cellname} -view ${gen.viewname} -cdslib ${env.CDS_LIB_PATH} -hdlvar ${env.CDS_HDLVAR_PATH} ${env.RUNAMS_OPTIONS} -rundir ${gen.rundir} -log ${gen.logfile}"

	def check_output(self,ret,out):
		for num,line in enumerate(out.split('\n')):
			if line.find('ERROR') == 0:
				Logs.error("Error in line %d: %s" % (num,line))
				ret = 1

		return ret

class auCdlTask(Task.Task):
	#run_str = 'rm -f .running && cp ${SRC[1].abspath()} si.env && cp si.env ${BRICK_RESULTS} && ${CADENCE_SI} -batch -command netlist'
	def run(self):

		run_str = 'rm -f .running && cp '+self.generator.si_env.abspath()+' si.env && cp si.env ${BRICK_RESULTS} && ${CADENCE_SI} -batch -command netlist'

		(f, dvars) = Task.compile_fun(run_str, False)
		return f(self)



#	def run(self):
#		split_path = Node.split_path(self.inputs[0].abspath())
#		split_path.reverse()
#		lib = split_path[3]
#		cell = split_path[2]
#		view = split_path[1]
#
#		cmd = 'amsdesigner -lib %s -cell %s -view %s -compile all -netlist all -rundir . -ncvlogopt "-use5x -64bit"' % (lib,cell,view)
#		return self.exec_command(cmd)
#
#	#def runnable_status(self):
#	#    pass

@TaskGen.feature('cds_netlist_sim')
def add_cds_netlist_target(self):
	try:
		cellview = getattr(self,'cellview','')
		if cellview.find('.') == -1 or cellview.find(':') == -1:
			Logs.error('Please specify a cellview of the form Lib:Cell:View with the \'view\' attribute with the feature \'cds_netlist\'.')
			return
		(self.libname,rest) = cellview.split(".")
		(self.cellname,self.viewname) = rest.split(":")

		try:
			config_file = self.path.find_dir(self.env['CDS_LIBS_FLAT'][self.libname])
		except KeyError:
			raise Errors.ConfigurationError('Please specify a library path for library '+self.libname+' in conf.env[\'CDS_LIBS\'], No library path found.')

		if not config_file:
			raise Errors.ConfigurationError('Library '+lib+' in '+selv.env['CDS_LIBS_FLAT'][self.libname]+' not found')
		config_file = config_file.make_node(self.cellname+'/'+self.viewname+'/expand.cfg')
		#if not config_file:
		#	raise Errors.ConfigurationError('Cellview '+self.cellname+':'+self.viewname+' in library '+self.libname+' not found.')

		# logfile
		self.logfile = self.env.BRICK_LOGFILES+'/cadence_netlist_'+self.cellname+'.log'

		self.rundir = self.cellname

		t = self.create_task('cdsNetlistTask', config_file)
	except ValueError:
		raise Errors.ConfigurationError('For feature "cds_netlist", you need to specify a parameter "toplevel" in the form of lib.cell:view')

@TaskGen.taskgen_method
def get_cds_netlist_lvs_node(self):
	lib,cell,view = self.get_cadence_lib_cell_view_from_cellview()
	lvs_netlist_filename = lib+'_'+cell+'.src.net'
	return self.bld.bldnode.find_node(self.env.BRICK_RESULTS).make_node(lvs_netlist_filename)

@TaskGen.feature('cds_netlist_lvs')
def add_cds_netlist_lvs_target(self):
	m0 = re.search('(\w+).(\w+):(\w+)', self.cellview)
	if not m0:
		Logs.error('Please specify a cellview of the form Lib:Cell:View with the \'view\' attribute with the feature \'cds_netlist_lvs\'.')
		return

	self.libname = m0.group(1)
	self.cellname = m0.group(2)
	self.viewname = m0.group(3)
	lvs_netlist_filename = self.libname+'_'+self.cellname+'.src.net'

	# the input file of the netlist task
	try:
		source_netlist = self.get_cellview_path(self.cellview).find_node('sch.oa')
	except AttributeError:
		raise Errors.WafError('Could not find schematic in cellview "'+self.cellview+'" in cds_netlist_lvs.')
		return 1
	if not source_netlist:
		raise Errors.WafError('Could not find schematic in cellview "'+self.cellview+'" in cds_netlist_lvs.')
		return 1
	# the configuration file for the netlister
	self.si_env = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'si.env_'+self.libname+'_'+self.cellname+'_'+self.viewname))
	# the output netlist
	lvs_netlist = self.get_cds_netlist_lvs_node()
	f1 = open(self.si_env.abspath(),"w")
	si_env_content = """
simLibName = "{0}"
simCellName = "{1}"
simViewName = "{2}"
simSimulator = "auCdl"
simNotIncremental = nil
simReNetlistAll = nil
simViewList = '("symbol" "schematic")
simStopList = '("symbol")
simNetlistHier = t
hnlNetlistFileName = "{3}"
simRunDir = "{4}"
resistorModel = " "
shortRES = 2000.0
preserveRES = 'nil
checkRESVAL = 'nil
checkRESSIZE = 'nil
preserveCAP = 'nil
checkCAPVAL = 'nil
checkCAPAREA = 'nil
preserveDIO = 'nil
checkDIOAREA = 'nil
checkDIOPERI = 'nil
displayPININFO = 'nil
preserveALL = 'nil
incFILE = "{5}"
setEQUIV = ""
	""".format(m0.group(1),m0.group(2),m0.group(3),lvs_netlist_filename,self.env.BRICK_RESULTS,getattr(self,'include',''))
	f1.write(si_env_content)
	f1.close()

	aucdl_task = self.create_task('auCdlTask',[source_netlist],lvs_netlist)




# vim: noexpandtab:
