import os,re
from waflib import Task,Errors,Node,TaskGen,Configure,Logs

def configure(conf):
	conf.load('cadence_base')

	conf.env.AMSDESIGNER = 'amsdesigner'
	if not conf.env.AMSDESIGNER_OPTIONS:
		conf.env.AMSDESIGNER_OPTIONS = [
				'-rundir', '.',
				'-ncvlogopts', '-use5x -64bit'
			]

	conf.env['CADENCE_SI'] = 'si'

class cdsNetlistTask(Task.Task):

	def run(self):
		"""Checking logfile for critical warnings line by line"""

		run_str = 'cd '+self.generator.path.get_bld().abspath()+' && ${AMSDESIGNER} -lib '+self.generator.libname+' -cell '+self.generator.cellname+' -view '+self.generator.viewname+' -compile all -netlist all -CDSLIB ${CDS_LIB_PATH} -hdlvar ${CDS_HDLVAR_PATH} ${AMSDESIGNER_OPTIONS}'

		(f, dvars) = Task.compile_fun(run_str, False)
		return f(self)

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
		cellview = getattr(self,'view','')
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

		t = self.create_task('cdsNetlistTask', config_file)
	except ValueError:
		raise Errors.ConfigurationError('For feature "cds_netlist", you need to specify a parameter "toplevel" in the form of lib.cell:view')

@TaskGen.feature('cds_netlist_lvs')
def add_cds_netlist_lvs_target(self):
	m0 = re.search('(\w+).(\w+):(\w+)', self.cellview)
	if m0:
		# the input file of the netlist task
		try:
			source_netlist = self.get_cellview_path(self.cellview).find_node('sch.oa')
		except AttributeError:
			Logs.error('Could not find cellview "'+self.cellview+'" in cds_netlist_lvs.')
			return
		# the configuration file for the netlister
		self.si_env = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'si.env_'+m0.group(1)+'_'+m0.group(2)+'_'+m0.group(3)))
		# the output netlist
		lvs_netlist_filename = m0.group(1)+'_'+m0.group(2)+'.src.net'
		lvs_netlist = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),self.env.BRICK_RESULTS,lvs_netlist_filename))
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
		""".format(m0.group(1),m0.group(2),m0.group(3),lvs_netlist_filename,self.env.BRICK_RESULTS,getattr(self,'include',''))#'/afs/kip.uni-heidelberg.de/cad/libs/tsmc/cdb/models/hspice/hspice.mdl')#/superfast/home/ahartel/chip-route65/env/include_all_models.scs')
		f1.write(si_env_content)
		f1.close()

		aucdl_task = self.create_task('auCdlTask',[source_netlist],lvs_netlist)
	else:
		Logs.error('Please specify a cellview of the form Lib:Cell:View with the \'view\' attribute with the feature \'cds_netlist_lvs\'.')




# vim: noexpandtab:
