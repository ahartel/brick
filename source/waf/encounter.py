import os
from waflib import Task,Errors,TaskGen,Configure,Node,Logs

class EncounterConfig:
	flow_settings = {}
	oa_ref_lib = []
	oa_search_lib = []
	opconds = []
	opcond_library = {}
	lef_files = []
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
			'target_hold_slack' : 0.1,
			'target_setup_slack' : 0.4,
			'drc_margin_factor' : 0.2,
			'enable_metalfill': False,
			'enable_qx' : True,
			'enable_rcgen' : False,
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

	def insert_flow_settings(self):
		from encounter_tcl import flow_settings_tcl
		return flow_settings_tcl.format(
			int(self.flow_settings['use_external_cts_spec']),
			int(self.flow_settings['use_lef_flow']),
			int(self.flow_settings['enable_iofill']),
			int(self.flow_settings['enable_corefill']),
			int(self.flow_settings['enable_load_floorplan']),
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

	def insert_place(self,setup_tcl,parameters,place_script):
		from encounter_tcl import steps_tcl
		try:
			return steps_tcl['place'].format(
					setup_tcl.abspath(),
					parameters.abspath(),
					'1',
					place.abspath(),
					)
		except:
			return steps_tcl['place'].format(
					setup_tcl.abspath(),
					parameters.abspath(),
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

	def insert_setup(self,toplevel,netlist,sdc,io_file,add_lef_files,add_lib_files,gds_map,lef_layermap,flow_settings):
		from encounter_tcl import setup_tcl
		return setup_tcl.format(
					toplevel,
					netlist.abspath(),
					sdc.abspath(),
					io_file.abspath(),
					'" \\\n"'.join(self.lef_files + add_lef_files),
					'" \\\n"'.join(self.max_timing_files + add_lib_files),
					'" \\\n"'.join(self.typ_timing_files + add_lib_files),
					'" \\\n"'.join(self.min_timing_files + add_lib_files),
					self.cap_tables['typ'],
					self.cap_tables['max'],
					self.cap_tables['min'],
					gds_map.abspath(),
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
			'target_hold_slack' : 0.1,
			'target_setup_slack' : 0.4,
			'drc_margin_factor' : 0.2,
			'enable_metalfill': False,
			'enable_qx' : True,
			'enable_rcgen' : False,
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
			# lib files
			[x.abspath() for x in getattr(self,'additional_timing_libraries',[])],
			self.gds_map,
			self.qx_leflayer_map,
			self.flowsetting_tcl_script,
		))

	self.corner_def_tcl_script = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'enc_corner_def_'+self.toplevel+'.tcl'))
	with open(self.corner_def_tcl_script.abspath(),'w') as f:
		f.write(config_object.insert_corner_def())

	# Bind step
	self.bind_tcl_script = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'enc_bind_'+self.toplevel+'.tcl'))
	with open(self.bind_tcl_script.abspath(),'w') as f:
		f.write(config_object.insert_bind(self.setup_tcl_script,self.corner_def_tcl_script))
	bind_task = self.create_task('EncounterBindTask',[self.netlist,self.constraints_file]+getattr(self,'additional_physical_libraries',[])+getattr(self,'additional_timing_libraries',[]),[results_dir.make_node(self.toplevel+'_bind.enc')])

	if getattr(self,'stop_tep','') == 'bind':
		return

	# Floorplan step
	self.floorplan_tcl_script = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'enc_floorplan_'+self.toplevel+'.tcl'))
	with open(self.floorplan_tcl_script.abspath(),'w') as f:
		f.write(config_object.insert_floorplan(self.setup_tcl_script,self.parameters,self.floorplan_mixin))
	fp_inputs = [results_dir.make_node(self.toplevel+'_bind.enc')]
	if hasattr(self,'io_file'):
		fp_inputs.append(self.io_file)
	floorplan_task = self.create_task('EncounterFloorplanTask',fp_inputs,[results_dir.make_node(self.toplevel+'_floorplan.enc')])

	if getattr(self,'stop_tep','') == 'floorplan':
		return

	# Place step
	self.place_tcl_script = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'enc_place_'+self.toplevel+'.tcl'))
	with open(self.place_tcl_script.abspath(),'w') as f:
		f.write(config_object.insert_place(self.setup_tcl_script,self.parameters,getattr(self,'place_mixin',None)))
	place_inputs = [results_dir.make_node(self.toplevel+'_floorplan.enc')]
	if hasattr(self,'place_mixin'):
		place_inputs.append(self.io_file)
	place_task = self.create_task('EncounterPlaceTask',place_inputs,[results_dir.make_node(self.toplevel+'_place.enc')])

	if getattr(self,'stop_tep','') == 'place':
		return

# vim: noexpandtab:

