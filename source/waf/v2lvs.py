import os
from brick_general import ChattyBrickTask
from waflib import Task,Errors,Node,TaskGen,Configure,Node,Logs,Context

def configure(conf):
	"""This function gets called by waf upon loading of this module in a configure method"""

	conf.load('brick_general')

	conf.find_program('v2lvs',var='MENTOR_V2LVS')
	conf.env['V2LVS_OPTIONS'] = [
		]

@TaskGen.feature('v2lvs')
def create_v2lvs_task(self):

	try:
		getattr(self,'verilog_netlist',None).abspath()
		getattr(self,'target_netlist',None).abspath()
	except AttributeError:
		Logs.error("Verilog netlist '"+getattr(self,'verilog_netlist','')+"' not found or traget netlist not given as Node object in v2lvs.")
		return

	inputs = [self.verilog_netlist]

	self.include_string = ''
	for filename in getattr(self,'include_netlists',[]):
		inputs.append(filename)
		if filename.suffix() == '.v':
			self.include_string += ' -v '+filename.abspath()
		elif filename.suffix() == '.net' or filename.suffix() == '.sp':
			self.include_string += ' -s '+filename.abspath()
		else:
			Logs.error('You have given a file as include_netlist for which I can not tell whether it\'s spice or verilog (I only know .v, .net and .sp). Filename '+filename.abspath()+' in tool v2lvs')
			return

	self.logfile = self.env['BRICK_LOGFILES']+'/'+os.path.basename(self.verilog_netlist.abspath())+'_v2lvs.log'

	t = self.create_task('v2lvsTask', inputs, self.target_netlist)

#@Task.always_run
class v2lvsTask(ChattyBrickTask):
	vars = ['MENTOR_V2LVS','V2LVS_OPTIONS']
	shell = True
	run_str = '${env.MENTOR_V2LVS} ${env.V2LVS_OPTIONS} -v ${SRC[0].abspath()} -log ${gen.logfile} -o ${gen.target_netlist.abspath()} ${gen.include_string}'



# vim: noexpandtab
