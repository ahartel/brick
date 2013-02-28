import os,re
from waflib import Task,Errors,Node,TaskGen,Configure,Node,Logs,Context

def configure(conf):
	conf.load('brick_general')

	"""This function gets called by waf upon loading of this module in a configure method"""
	if not conf.env.BRICK_LOGFILES:
		conf.env.BRICK_LOGFILES = './logfiles'
	conf.env['V2LVS'] = 'v2lvs'
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
	inputs += getattr(self,'include_netlists',[])

	t = self.create_task('v2lvsTask', inputs, self.target_netlist)

@Task.always_run
class v2lvsTask(Task.Task):
	vars = ['V2LVS','V2LVS_OPTIONS']

	def run(self):

		run_str = '%s -v %s -log %s -o %s' % (self.env.V2LVS, self.inputs[0].abspath(),self.env.BRICK_LOGFILES+'/'+self.generator.name+'_v2lvs.log',self.generator.target_netlist.abspath())

		if hasattr(self.generator,'include_netlists'):
			for filename in self.generator.include_netlists:
				if filename.suffix() == '.v':
					run_str += ' -v '+filename.abspath()
				elif filename.suffix() == '.net' or filename.suffix() == '.sp':
					run_str += ' -s '+filename.abspath()
				else:
					Logs.error('You have given a file as include_netlist for which I can not tell whether it\'s spice or verilog (I only know .v, .net and .sp). Filename '+filename.abspath()+' in tool v2lvs')
					return

		try:
			out = self.generator.bld.cmd_and_log(run_str, quiet=Context.STDOUT)
		except Exception as e:
			out = e.stderr


# for convenience
@Configure.conf
def v2lvs(bld,*k,**kw):
	set_features(kw,'v2lvs')
	return bld(*k,**kw)

# vim: noexpandtab
