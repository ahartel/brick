import os
from waflib import Task,Errors,TaskGen,Configure,Node,Logs

class EncounterConfig:
	flow_settings = {}
	oa_ref_lib = []
	oa_search_lib = []
	opconds = []
	opcond_library = {}
	lef_files = []
	gds_files = []
	max_timing_files = []
	typ_timing_files = []
	min_timing_files = []
	cap_tables = {}
	qx_tech_files = {}

	def __init__(self):
		self.flow_settings = {
			'use_external_cts_spec' : False,
			'use_lef_flow' : True,
			'enable_iofill' : True,
			'enable_corefill' : True,
			'enable_load_floorplan' : False,
			'enable_route_clk_first' : False,
			'target_hold_slack' : 0.1,
			'target_setup_slack' : 0.4,
			'drc_margin_factor' : 0.2,
			'enable_metalfill': False,
			'enable_qx' : True,
			'enable_rcgen' : True,
			'enable_si' : True,
			'enable_usefulskew' : False,
			'enable_ocv' : False,
			}

		self.opconds = ['WCCOM','NCCOM','BCCOM']
		self.opcond_library['WCCOM'] = 'undefined_wc'
		self.opcond_library['NCCOM'] = 'undefined_tc'
		self.opcond_library['BCCOM'] = 'undefined_bc'

		self.cap_tables = {'typ':'undefined_typ','max':'undefined_max','min':'undefined_min'}
		self.qx_tech_files = {'rctyp':'undefined_typ','max':'undefined_max','min':'undefined_min'}

		self.clk_buffer_list = []
		self.hold_buffer_list = []

	def insert_flow_settings(self):
		from encounter_tcl import flow_settings_tcl
		return flow_settings_tcl.format(
			int(self.flow_settings['use_external_cts_spec']),
			int(self.flow_settings['use_lef_flow']),
			int(self.flow_settings['enable_iofill']),
			int(self.flow_settings['enable_corefill']),
			int(self.flow_settings['enable_load_floorplan']),
			int(self.flow_settings['enable_route_clk_first']),
			self.flow_settings['target_hold_slack'],
			self.flow_settings['target_setup_slack'],
			self.flow_settings['drc_margin_factor'],
			int(self.flow_settings['enable_metalfill']),
			int(self.flow_settings['enable_qx']),
			int(self.flow_settings['enable_rcgen']),
			int(self.flow_settings['enable_si']),
			int(self.flow_settings['enable_usefulskew']),
			int(self.flow_settings['enable_ocv']))


	def insert_bind(self,setup_tcl,corner_tcl):
		from encounter_tcl import steps_tcl
		return steps_tcl['bind'].format(
				setup_tcl.abspath(),
				corner_tcl.abspath(),
				" ".join(self.oa_ref_lib),
				" ".join(self.oa_search_lib),
				)

	def insert_floorplan(self,setup_tcl,parameters,fp_script):
		from encounter_tcl import steps_tcl
		try:
			return steps_tcl['floorplan'].format(
					setup_tcl.abspath(),
					parameters.abspath(),
					'1',
					fp_script.abspath(),
					)
		except:
			return steps_tcl['floorplan'].format(
					setup_tcl.abspath(),
					parameters.abspath(),
					'0',
					'',
					)

	def insert_place(self,setup_tcl,parameters,place_script,cts_spec):
		from encounter_tcl import steps_tcl
		try:
			return steps_tcl['place'].format(
					setup_tcl.abspath(),
					parameters.abspath(),
					'1',
					place_script.abspath(),
					cts_spec.abspath()
					)
		except:
			return steps_tcl['place'].format(
					setup_tcl.abspath(),
					parameters.abspath(),
					'0',
					'',
					cts_spec.abspath()
					)

	def insert_prects(self,setup_tcl,prects_script,rc_factors):
		from encounter_tcl import steps_tcl
		try:
			return steps_tcl['prects'].format(
					setup_tcl.abspath(),
					'1',
					prects_script.abspath(),
					rc_factors.abspath()
					)
		except:
			return steps_tcl['prects'].format(
					setup_tcl.abspath(),
					'0',
					'',
					rc_factors.abspath()
					)

	def insert_cts(self,setup_tcl,cts_script,cts_spec):
		from encounter_tcl import steps_tcl
		try:
			return steps_tcl['cts'].format(
					setup_tcl.abspath(),
					'1',
					cts_script.abspath(),
					cts_spec.abspath()
					)
		except:
			return steps_tcl['cts'].format(
					setup_tcl.abspath(),
					'0',
					'',
					cts_spec.abspath()
					)

	def insert_postcts(self,setup_tcl,postcts_script,rc_factors):
		from encounter_tcl import steps_tcl
		try:
			return steps_tcl['postcts'].format(
					setup_tcl.abspath(),
					'1',
					postcts_script.abspath(),
					rc_factors.abspath()
					)
		except:
			return steps_tcl['postcts'].format(
					setup_tcl.abspath(),
					'0',
					'',
					rc_factors.abspath()
					)

	def insert_route(self,setup_tcl,route_script):
		from encounter_tcl import steps_tcl
		try:
			return steps_tcl['route'].format(
					setup_tcl.abspath(),
					'1',
					route_script.abspath()
					)
		except:
			return steps_tcl['route'].format(
					setup_tcl.abspath(),
					'0',
					''
					)

	def insert_postroute(self,setup_tcl,postroute_script,rc_factors):
		from encounter_tcl import steps_tcl
		try:
			return steps_tcl['postroute'].format(
					setup_tcl.abspath(),
					'1',
					postroute_script.abspath(),
					rc_factors.abspath()
					)
		except:
			return steps_tcl['postroute'].format(
					setup_tcl.abspath(),
					'0',
					'',
					rc_factors.abspath()
					)

	def insert_final(self,setup_tcl,parameters,final_script):
		from encounter_tcl import steps_tcl
		try:
			return steps_tcl['final'].format(
					setup_tcl.abspath(),
					parameters.abspath(),
					'1',
					final_script.abspath(),
					)
		except:
			return steps_tcl['final'].format(
					setup_tcl.abspath(),
					parameters.abspath(),
					'0',
					'',
					)

	def insert_extract(self,setup_tcl,extract_script,qrc_type,qrc_file):
		from encounter_tcl import steps_tcl
		try:
			return steps_tcl['extract'].format(
					setup_tcl.abspath(),
					'1',
					extract_script.abspath(),
					1 if qrc_type else 0,
					str(qrc_type),
					qrc_file.abspath() if qrc_type else '',
					)
		except:
			return steps_tcl['extract'].format(
					setup_tcl.abspath(),
					'0',
					'',
					1 if qrc_type else 0,
					str(qrc_type),
					qrc_file.abspath() if qrc_type else '',
					)

	def insert_streamout(self,setup_tcl,streamout_script):
		from encounter_tcl import steps_tcl
		try:
			return steps_tcl['streamout'].format(
					setup_tcl.abspath(),
					'1',
					streamout_script.abspath(),
					)
		except:
			return steps_tcl['streamout'].format(
					setup_tcl.abspath(),
					'0',
					'',
					)

	def insert_corner_def(self):
		from encounter_tcl import corner_def_tcl
		return corner_def_tcl.format(
				self.opcond_library[self.opconds[0]],
				self.opconds[0],
				self.opcond_library[self.opconds[1]],
				self.opconds[1],
				self.opcond_library[self.opconds[2]],
				self.opconds[2],
				)

	def insert_setup(self,toplevel,netlist,sdc,io_file,add_lef_files,add_gds_files,add_lib_files,gds_map,lef_layermap,flow_settings):
		from encounter_tcl import setup_tcl
		return setup_tcl.format(
					toplevel,
					netlist.abspath(),
					sdc.abspath(),
					io_file.abspath(),
					'" \\\n"'.join(self.lef_files + add_lef_files),
					'" \\\n"'.join(self.gds_files + add_gds_files),
					'" \\\n"'.join(self.max_timing_files + add_lib_files),
					'" \\\n"'.join(self.typ_timing_files + add_lib_files),
					'" \\\n"'.join(self.min_timing_files + add_lib_files),
					self.cap_tables['typ'],
					self.cap_tables['max'],
					self.cap_tables['min'],
					gds_map.abspath(),
					' '.join(self.clk_buffer_list),
					' '.join(self.hold_buffer_list),
					self.qx_tech_files['rctyp'],
					self.qx_tech_files['rcworst'],
					self.qx_tech_files['rcbest'],
					lef_layermap.abspath(),
					flow_settings.abspath(),
				)


class EncounterTSMCConfig(EncounterConfig):
	def __init__(self):
		self.flow_settings = {
			'use_external_cts_spec' : False,
			'use_lef_flow' : True,
			'enable_iofill' : True,
			'enable_corefill' : True,
			'enable_load_floorplan' : False,
			'enable_route_clk_first' : False,
			'target_hold_slack' : 0.1,
			'target_setup_slack' : 0.4,
			'drc_margin_factor' : 0.2,
			'enable_metalfill': False,
			'enable_qx' : True,
			'enable_rcgen' : True,
			'enable_si' : True,
			'enable_usefulskew' : False,
			'enable_ocv' : False,
			}

		self.opconds = ['WCCOM','NCCOM','BCCOM']
		self.opcond_library['WCCOM'] = 'tcbn65lpwc'
		self.opcond_library['NCCOM'] = 'tcbn65lptc'
		self.opcond_library['BCCOM'] = 'tcbn65lpbc'

		self.cap_tables = {
				'typ':'/cad/libs/tsmc/encounter/captbl/tsmc_crn65lp_1p09m+alrdl_6x1z1u_typ_extended.captbl',
				'max':'/cad/libs/tsmc/encounter/captbl/tsmc_crn65lp_1p09m+alrdl_6x1z1u_typ_extended.captbl',
				'min':'/cad/libs/tsmc/encounter/captbl/tsmc_crn65lp_1p09m+alrdl_6x1z1u_typ_extended.captbl'
			}

		self.qx_tech_files = {
				'rctyp': '/cad/libs/tsmc/imec_online/CMN65LP/t-n65-cm-sp-007-v1_1_3a/1p9m_6x1z1u/typical/qrcTechFile',
				'rcworst': '/cad/libs/tsmc/imec_online/CMN65LP/t-n65-cm-sp-007-v1_1_3a/1p9m_6x1z1u/rcworst/qrcTechFile',
				'rcbest': '/cad/libs/tsmc/imec_online/CMN65LP/t-n65-cm-sp-007-v1_1_3a/1p9m_6x1z1u/rcbest/qrcTechFile'
			}

		self.lef_files = [
				"/cad/libs/tsmc/digital/Back_End/lef/tcbn65lp_200a/lef/tcbn65lp_9lmT2.lef",
#				"/cad/libs/tsmc/digital/Back_End/lef/tpdn65lpnv2_140b/mt_2/9lm/lef/tpdn65lpnv2_9lm.lef",
				"/cad/libs/tsmc/digital/Back_End/lef/tpdn65lpnv2_140b/mt_2/9lm/lef/antenna_9lm.lef",
				"/cad/libs/tsmc/digital/Back_End/lef/tpan65lpnv2_140b/mt_2/9lm/lef/antenna_9lm.lef",
				"/cad/libs/tsmc/asic_lab/lef4soc/tpan65lpnv2_9lm.mod.lef",
				"/cad/libs/tsmc/asic_lab/lef4soc/tpdn65lpnv2_9lm.mod.lef",

#				"/cad/libs/tsmc/digital/Back_End/lef/tpan65lpnv2_140b/mt/9lm/lef/tpan65lpnv2_9lm.lef",
			]


		self.clk_buffer_list = ["CKBD1", 'CKBD2', 'CKBD3', 'CKBD4', 'CKBD6', 'CKBD8', 'CKBD12', 'CKBD16']
		self.hold_buffer_list = ['DEL0', 'DEL1', 'DEL2', 'DEL3', 'DEL4', 'DEL02', 'DEL015', 'DEL01', 'DEL005']

		self.gds_files = [
				"/cad/libs/tsmc/asic_lab/gds4lvs/tpan65lpnv2_9lm.mod.lef.gds",
				"/cad/libs/tsmc/asic_lab/gds4lvs/tpdn65lpnv2_9lm.mod.lef.gds",
			]

		self.max_timing_files = [
				"/cad/libs/tsmc/digital/Front_End/timing_power_noise/NLDM/tcbn65lp_200a/tcbn65lpwc.lib",
				"/cad/libs/tsmc/digital/Front_End/timing_power_noise/NLDM/tpan65lpnv2_140b/tpan65lpnv2wc.lib",
				"/cad/libs/tsmc/digital/Front_End/timing_power_noise/NLDM/tpdn65lpnv2_140b/tpdn65lpnv2wc.lib",
			]

		self.typ_timing_files = [
				"/cad/libs/tsmc/digital/Front_End/timing_power_noise/NLDM/tcbn65lp_200a/tcbn65lptc.lib",
				"/cad/libs/tsmc/digital/Front_End/timing_power_noise/NLDM/tpan65lpnv2_140b/tpan65lpnv2tc.lib",
				"/cad/libs/tsmc/digital/Front_End/timing_power_noise/NLDM/tpdn65lpnv2_140b/tpdn65lpnv2tc.lib",
			]
		self.min_timing_files = [
				"/cad/libs/tsmc/digital/Front_End/timing_power_noise/NLDM/tcbn65lp_200a/tcbn65lpbc.lib",
				"/cad/libs/tsmc/digital/Front_End/timing_power_noise/NLDM/tpan65lpnv2_140b/tpan65lpnv2bc.lib",
				"/cad/libs/tsmc/digital/Front_End/timing_power_noise/NLDM/tpdn65lpnv2_140b/tpdn65lpnv2bc.lib",
			]

class EncounterBindTask(Task.Task):
	vars = ['ENCOUNTER','ENCOUNTER_OPTIONS']
	def run(self):
		logfile = self.generator.path.get_bld().make_node(os.path.join(self.generator.path.bld_dir(),self.env.BRICK_LOGFILES,'encounter_bind.log'))
		run_str = '%s %s -init %s -log %s' % (self.env.ENCOUNTER," ".join(self.env.ENCOUNTER_OPTIONS),self.generator.bind_tcl_script.abspath(),logfile.abspath())

		try:
			out = self.generator.bld.cmd_and_log(run_str)#, quiet=Context.STDOUT)
		except Exception as e:
			out = e.stdout + e.stderr

class EncounterFloorplanTask(Task.Task):
	vars = ['ENCOUNTER','ENCOUNTER_OPTIONS']
	def run(self):
		logfile = self.generator.path.get_bld().make_node(os.path.join(self.generator.path.bld_dir(),self.env.BRICK_LOGFILES,'encounter_floorplan.log'))
		run_str = '%s %s -init %s -log %s' % (self.env.ENCOUNTER," ".join(self.env.ENCOUNTER_OPTIONS),self.generator.floorplan_tcl_script.abspath(),logfile.abspath())

		try:
			out = self.generator.bld.cmd_and_log(run_str)#, quiet=Context.STDOUT)
		except Exception as e:
			out = e.stdout + e.stderr

class EncounterPlaceTask(Task.Task):
	vars = ['ENCOUNTER','ENCOUNTER_OPTIONS']
	def run(self):
		logfile = self.generator.path.get_bld().make_node(os.path.join(self.generator.path.bld_dir(),self.env.BRICK_LOGFILES,'encounter_place.log'))
		run_str = '%s %s -init %s -log %s' % (self.env.ENCOUNTER," ".join(self.env.ENCOUNTER_OPTIONS),self.generator.place_tcl_script.abspath(),logfile.abspath())

		try:
			out = self.generator.bld.cmd_and_log(run_str)#, quiet=Context.STDOUT)
		except Exception as e:
			out = e.stdout + e.stderr

class EncounterPrectsTask(Task.Task):
	vars = ['ENCOUNTER','ENCOUNTER_OPTIONS']
	def run(self):
		logfile = self.generator.path.get_bld().make_node(os.path.join(self.generator.path.bld_dir(),self.env.BRICK_LOGFILES,'encounter_prects.log'))
		run_str = '%s %s -init %s -log %s' % (self.env.ENCOUNTER," ".join(self.env.ENCOUNTER_OPTIONS),self.generator.prects_tcl_script.abspath(),logfile.abspath())

		try:
			out = self.generator.bld.cmd_and_log(run_str)#, quiet=Context.STDOUT)
		except Exception as e:
			out = e.stdout + e.stderr

class EncounterCtsTask(Task.Task):
	vars = ['ENCOUNTER','ENCOUNTER_OPTIONS']
	def run(self):
		logfile = self.generator.path.get_bld().make_node(os.path.join(self.generator.path.bld_dir(),self.env.BRICK_LOGFILES,'encounter_cts.log'))
		run_str = '%s %s -init %s -log %s' % (self.env.ENCOUNTER," ".join(self.env.ENCOUNTER_OPTIONS),self.generator.cts_tcl_script.abspath(),logfile.abspath())

		try:
			out = self.generator.bld.cmd_and_log(run_str)#, quiet=Context.STDOUT)
		except Exception as e:
			out = e.stdout + e.stderr

class EncounterPostctsTask(Task.Task):
	vars = ['ENCOUNTER','ENCOUNTER_OPTIONS']
	def run(self):
		logfile = self.generator.path.get_bld().make_node(os.path.join(self.generator.path.bld_dir(),self.env.BRICK_LOGFILES,'encounter_postcts.log'))
		run_str = '%s %s -init %s -log %s' % (self.env.ENCOUNTER," ".join(self.env.ENCOUNTER_OPTIONS),self.generator.postcts_tcl_script.abspath(),logfile.abspath())

		try:
			out = self.generator.bld.cmd_and_log(run_str)#, quiet=Context.STDOUT)
		except Exception as e:
			out = e.stdout + e.stderr

class EncounterRouteTask(Task.Task):
	vars = ['ENCOUNTER','ENCOUNTER_OPTIONS']
	def run(self):
		logfile = self.generator.path.get_bld().make_node(os.path.join(self.generator.path.bld_dir(),self.env.BRICK_LOGFILES,'encounter_route.log'))
		run_str = '%s %s -init %s -log %s' % (self.env.ENCOUNTER," ".join(self.env.ENCOUNTER_OPTIONS),self.generator.route_tcl_script.abspath(),logfile.abspath())

		try:
			out = self.generator.bld.cmd_and_log(run_str)#, quiet=Context.STDOUT)
		except Exception as e:
			out = e.stdout + e.stderr

class EncounterPostrouteTask(Task.Task):
	vars = ['ENCOUNTER','ENCOUNTER_OPTIONS']
	def run(self):
		logfile = self.generator.path.get_bld().make_node(os.path.join(self.generator.path.bld_dir(),self.env.BRICK_LOGFILES,'encounter_postroute.log'))
		run_str = '%s %s -init %s -log %s' % (self.env.ENCOUNTER," ".join(self.env.ENCOUNTER_OPTIONS),self.generator.postroute_tcl_script.abspath(),logfile.abspath())

		try:
			out = self.generator.bld.cmd_and_log(run_str)#, quiet=Context.STDOUT)
		except Exception as e:
			out = e.stdout + e.stderr

class EncounterFinalTask(Task.Task):
	vars = ['ENCOUNTER','ENCOUNTER_OPTIONS']
	def run(self):
		logfile = self.generator.path.get_bld().make_node(os.path.join(self.generator.path.bld_dir(),self.env.BRICK_LOGFILES,'encounter_final.log'))
		run_str = '%s %s -init %s -log %s' % (self.env.ENCOUNTER," ".join(self.env.ENCOUNTER_OPTIONS),self.generator.final_tcl_script.abspath(),logfile.abspath())

		try:
			out = self.generator.bld.cmd_and_log(run_str)#, quiet=Context.STDOUT)
		except Exception as e:
			out = e.stdout + e.stderr

class EncounterExtractTask(Task.Task):
	vars = ['ENCOUNTER','ENCOUNTER_OPTIONS']
	def run(self):
		logfile = self.generator.path.get_bld().make_node(os.path.join(self.generator.path.bld_dir(),self.env.BRICK_LOGFILES,'encounter_extract.log'))
		run_str = '%s %s -init %s -log %s' % (self.env.ENCOUNTER," ".join(self.env.ENCOUNTER_OPTIONS),self.generator.extract_tcl_script.abspath(),logfile.abspath())

		try:
			out = self.generator.bld.cmd_and_log(run_str)#, quiet=Context.STDOUT)
		except Exception as e:
			out = e.stdout + e.stderr

class EncounterStreamoutTask(Task.Task):
	vars = ['ENCOUNTER','ENCOUNTER_OPTIONS']
	def run(self):
		logfile = self.generator.path.get_bld().make_node(os.path.join(self.generator.path.bld_dir(),self.env.BRICK_LOGFILES,'encounter_streamout.log'))
		run_str = '%s %s -init %s -log %s' % (self.env.ENCOUNTER," ".join(self.env.ENCOUNTER_OPTIONS),self.generator.streamout_tcl_script.abspath(),logfile.abspath())

		try:
			out = self.generator.bld.cmd_and_log(run_str)#, quiet=Context.STDOUT)
		except Exception as e:
			out = e.stdout + e.stderr 

def configure(conf):
	conf.load('brick_general')
	if not conf.env.BRICK_LOGFILES:
		conf.env.BRICK_LOGFILES = './logfiles'
	conf.env['ENCOUNTER'] = 'encounter'
	conf.env['ENCOUNTER_OPTIONS'] = ['-nowin','-overwrite']


@TaskGen.feature('encounter')
def create_encounter_task(self):

	config_object = EncounterTSMCConfig()

	if not hasattr(self,'toplevel'):
		Logs.error('You have not specified a toplevel module for an Encounter run.')
		return

	results_dir = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),self.env.BRICK_RESULTS,self.toplevel+'_enc'))

	self.flowsetting_tcl_script = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'enc_flow_settings_'+self.toplevel+'.tcl'))

	self.prects_rc_factors = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'enc_prects_rc_factors'+self.toplevel+'.tcl'))
	self.postroute_rc_factors = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'enc_postroute_rc_factors'+self.toplevel+'.tcl'))

	self.cts_spec = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'enc_cts_'+self.toplevel+'.spec'))

	with open(self.flowsetting_tcl_script.abspath(),'w') as f:
		f.write(config_object.insert_flow_settings())

	self.setup_tcl_script = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'enc_setup_'+self.toplevel+'.tcl'))
	with open(self.setup_tcl_script.abspath(),'w') as f:
		f.write(config_object.insert_setup(
			self.toplevel,
			self.netlist,
			self.constraints_file,
			self.io_file,
			# lef files
			[x.abspath() for x in getattr(self,'additional_physical_libraries',[])],
			# gds files
			[x.abspath() for x in getattr(self,'additional_gds_files',[])],
			# lib files
			[x.abspath() for x in getattr(self,'additional_timing_libraries',[])],
			self.gds_map,
			self.qx_leflayer_map,
			self.flowsetting_tcl_script,
		))

	self.corner_def_tcl_script = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'enc_corner_def_'+self.toplevel+'.tcl'))
	with open(self.corner_def_tcl_script.abspath(),'w') as f:
		f.write(config_object.insert_corner_def())

	self.qrc_cmd_file = getattr(self,'qrc_cmd_file',None)
	self.qrc_cmd_type = getattr(self,'qrc_cmd_type',None)

	# Bind step
	self.bind_tcl_script = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'enc_bind_'+self.toplevel+'.tcl'))
	with open(self.bind_tcl_script.abspath(),'w') as f:
		f.write(config_object.insert_bind(self.setup_tcl_script,self.corner_def_tcl_script))
	bind_task = self.create_task('EncounterBindTask',[self.netlist,self.constraints_file]+getattr(self,'additional_physical_libraries',[])+getattr(self,'additional_timing_libraries',[]),[results_dir.make_node(self.toplevel+'_bind.enc')])

	if getattr(self,'stop_step','') == 'bind':
		return

	# Floorplan step
	self.floorplan_tcl_script = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'enc_floorplan_'+self.toplevel+'.tcl'))
	with open(self.floorplan_tcl_script.abspath(),'w') as f:
		f.write(config_object.insert_floorplan(self.setup_tcl_script,self.parameters,getattr(self,'floorplan_mixin',None)))
	fp_inputs = [results_dir.make_node(self.toplevel+'_bind.enc')]
	if hasattr(self,'io_file'):
		fp_inputs.append(self.io_file)
	if hasattr(self,'floorplan_mixin'):
		fp_inputs.append(self.floorplan_mixin)
	floorplan_task = self.create_task('EncounterFloorplanTask',fp_inputs,[results_dir.make_node(self.toplevel+'_floorplan.enc')])

	if getattr(self,'stop_step','') == 'floorplan':
		return

	# Place step
	self.place_tcl_script = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'enc_place_'+self.toplevel+'.tcl'))
	with open(self.place_tcl_script.abspath(),'w') as f:
		f.write(config_object.insert_place(self.setup_tcl_script,self.parameters,getattr(self,'place_mixin',None),self.cts_spec))
	place_inputs = [results_dir.make_node(self.toplevel+'_floorplan.enc')]
	if hasattr(self,'place_mixin'):
		place_inputs.append(self.io_file)
	place_task = self.create_task('EncounterPlaceTask',place_inputs,[results_dir.make_node(self.toplevel+'_place.enc')])

	if getattr(self,'stop_step','') == 'place':
		return

	# prects step
	self.prects_tcl_script = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'enc_prects_'+self.toplevel+'.tcl'))
	with open(self.prects_tcl_script.abspath(),'w') as f:
		f.write(config_object.insert_prects(self.setup_tcl_script,getattr(self,'prects_mixin',None),self.prects_rc_factors))
	prects_inputs = [results_dir.make_node(self.toplevel+'_place.enc')]
	if hasattr(self,'prects_mixin'):
		prects_inputs.append(self.io_file)
	prects_task = self.create_task('EncounterPrectsTask',prects_inputs,[results_dir.make_node(self.toplevel+'_prects.enc')])

	if getattr(self,'stop_step','') == 'prects':
		return

	# cts step
	self.cts_tcl_script = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'enc_cts_'+self.toplevel+'.tcl'))
	with open(self.cts_tcl_script.abspath(),'w') as f:
		f.write(config_object.insert_cts(self.setup_tcl_script,getattr(self,'cts_mixin',None),self.cts_spec))
	cts_inputs = [results_dir.make_node(self.toplevel+'_prects.enc')]
	if hasattr(self,'cts_mixin'):
		cts_inputs.append(self.io_file)
	cts_task = self.create_task('EncounterCtsTask',cts_inputs,[results_dir.make_node(self.toplevel+'_cts.enc')])

	if getattr(self,'stop_step','') == 'cts':
		return

	# postcts step
	self.postcts_tcl_script = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'enc_postcts_'+self.toplevel+'.tcl'))
	with open(self.postcts_tcl_script.abspath(),'w') as f:
		f.write(config_object.insert_postcts(self.setup_tcl_script,getattr(self,'postcts_mixin',None),self.prects_rc_factors))
	postcts_inputs = [results_dir.make_node(self.toplevel+'_cts.enc')]
	if hasattr(self,'postcts_mixin'):
		postcts_inputs.append(self.io_file)
	postcts_task = self.create_task('EncounterPostctsTask',postcts_inputs,[results_dir.make_node(self.toplevel+'_postcts.enc')])

	if getattr(self,'stop_step','') == 'postcts':
		return

	# route step
	self.route_tcl_script = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'enc_route_'+self.toplevel+'.tcl'))
	with open(self.route_tcl_script.abspath(),'w') as f:
		f.write(config_object.insert_route(self.setup_tcl_script,getattr(self,'route_mixin',None)))
	route_inputs = [results_dir.make_node(self.toplevel+'_postcts.enc')]
	if hasattr(self,'route_mixin'):
		route_inputs.append(self.io_file)
	route_task = self.create_task('EncounterRouteTask',route_inputs,[results_dir.make_node(self.toplevel+'_route.enc')])

	if getattr(self,'stop_step','') == 'route':
		return

	# postroute step
	self.postroute_tcl_script = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'enc_postroute_'+self.toplevel+'.tcl'))
	with open(self.postroute_tcl_script.abspath(),'w') as f:
		f.write(config_object.insert_postroute(self.setup_tcl_script,getattr(self,'postroute_mixin',None),self.postroute_rc_factors))
	postroute_inputs = [results_dir.make_node(self.toplevel+'_route.enc')]
	if hasattr(self,'postroute_mixin'):
		postroute_inputs.append(self.io_file)
	postroute_task = self.create_task('EncounterPostrouteTask',postroute_inputs,[results_dir.make_node(self.toplevel+'_postroute.enc')])

	if getattr(self,'stop_step','') == 'postroute':
		return

	# final step
	self.final_tcl_script = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'enc_final_'+self.toplevel+'.tcl'))
	with open(self.final_tcl_script.abspath(),'w') as f:
		f.write(config_object.insert_final(self.setup_tcl_script,self.parameters,getattr(self,'final_mixin',None)))
	final_inputs = [results_dir.make_node(self.toplevel+'_postroute.enc')]
	if hasattr(self,'final_mixin'):
		final_inputs.append(self.io_file)
	final_task = self.create_task('EncounterFinalTask',final_inputs,[results_dir.make_node(self.toplevel+'_final.enc')])

	if getattr(self,'stop_step','') == 'final':
		return

	# extract step
	self.extract_tcl_script = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'enc_extract_'+self.toplevel+'.tcl'))
	with open(self.extract_tcl_script.abspath(),'w') as f:
		f.write(config_object.insert_extract(self.setup_tcl_script,getattr(self,'extract_mixin',None),self.qrc_cmd_type,self.qrc_cmd_file))
	extract_inputs = [results_dir.make_node(self.toplevel+'_final.enc')]
	if hasattr(self,'extract_mixin'):
		extract_inputs.append(self.io_file)
	extract_task = self.create_task('EncounterExtractTask',extract_inputs,[results_dir.make_node('../extraction/'+self.toplevel+'_RCTYP.spef.gz'),results_dir.make_node('../encounter_'+self.toplevel+'.sdf.gz')])

	if getattr(self,'stop_step','') == 'extract':
		return

	# streamout step
	self.streamout_tcl_script = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'enc_streamout_'+self.toplevel+'.tcl'))
	with open(self.streamout_tcl_script.abspath(),'w') as f:
		f.write(config_object.insert_streamout(self.setup_tcl_script,getattr(self,'streamout_mixin',None)))
	streamout_inputs = [results_dir.make_node(self.toplevel+'_final.enc')]
	if hasattr(self,'streamout_mixin'):
		streamout_inputs.append(self.io_file)
	streamout_task = self.create_task('EncounterStreamoutTask',streamout_inputs,[results_dir.make_node('../encounter_'+self.toplevel+'.v'),results_dir.make_node('../encounter_'+self.toplevel+'.sdc'),results_dir.make_node('../encounter_'+self.toplevel+'.gds')])

	if getattr(self,'stop_step','') == 'streamout':
		return

# vim: noexpandtab:

