import os,re
from waflib import Task,Errors,Node,TaskGen,Configure,Node,Logs

def configure(conf):
	"""This function gets called by waf upon loading of this module in a configure method"""

	conf.load('brick_general')

	if not conf.env.BRICK_LOGFILES:
		conf.env.BRICK_LOGFILES = './logfiles'
	conf.env['CADENCE_ABSTRACT'] = 'abstract'
	conf.env['CADENCE_ABSTRACT_OPTIONS'] = [
			'-nogui',
		]


@TaskGen.feature('cds_absgen')
def create_cadence_absgen_task(self):

    # extract lib, cell and view
	cellview = getattr(self,'cellview','')
	if cellview.find('.') == -1 or cellview.find(':') == -1:
		Logs.error('Please specify a cellview of the form Lib:Cell:View with the \'cellview\' attribute with the feature \'cds_absgen\'.')
		return
	(self.libname,rest) = cellview.split(".")
	(self.cellname,self.viewname) = rest.split(":")

	# prepare nodes for script, layout and lef file
	self.absgen_script = self.path.get_bld().make_node('absgen_'+self.libname+'_'+self.cellname+'.il')
	input_layout_node = self.get_cellview_path(cellview).find_node('layout.oa')
	export_lef_file = getattr(self,'export_lef_file',None)

	# generate some default options if none are given by the user
	if not hasattr(self,'abstract_options'):
		self.abstract_options = { 'Block': {
			'AbstractBlockageShrinkWrapLayers': "(M9 M9) (M8 M8) (M7 M7) (M6 M6) (M5 M5) (M4 M4) (M3 M3) (M2 M2)",
			'AbstractBlockageShrinkAdjust': "(M9 1) (M8 1) (M7 1) (M6 1) (M5 1) (M4 1) (M3 1) (M2 1)",
			'AbstractBlockageCoverLayers': "(M1 M1)",
			'AbstractBlockageCoverLayersDist': "(M1 1)",

			'AbstractBlockagePinCutWindow': "(M1 0.15) (M2 0.15) (M3 0.15) (M4 0.15) (M5 0.15) (M6 0.15) (M7 0.15)",
			'AbstractBlockageDownPinCutWindow': "(M1 0.15) (M2 0.15) (M3 0.15) (M4 0.15) (M5 0.15) (M6 0.15) (M7 0.15) ",
			'AbstractBlockageCutAroundPin': "M1 M2 M3 M4 M5 M6 M7",

			"PinsTextManipulation": "",
			'PinsPowerNames': "vdd12d",
			'PinsGroundNames': "gnd:d",
			'PinsClockNames': "",
			'PinsAnalogNames': "",
			'PinsOutputNames': "",
			'PinsTextPinMap': "((M1 pin) (M1 drawing)) ((M2 pin) (M2 drawing)) ((M3 pin) (M3 drawing)) ((M4 pin) (M4 drawing)) ((M5 pin) (M5 drawing)) ((M6 pin) (M6 drawing)) ((M7 pin) (M7 drawing))",
			'ExtractConnectivity': "(M1 M2 VIA1)(M2 M3 VIA2)(M3 M4 VIA3)(M4 M5 VIA4)(M5 M6 VIA5)",
			}
		}

	f = open(self.absgen_script.abspath(),"w")
	f.write("""
absSkillMode()
absSetOption("DefaultBin" "Block")
absSetLibrary("{0}")
absSelectAllBins()
absSelectCells()
absMoveSelectedCellsToBin("Ignore")
absDeselectCells()
absDeselectAllBins()
absSelectBin("Ignore")
absSelectCell("{1}")
""".format(self.libname,self.cellname))

	f.write("""
;        absMoveSelectedCellsToBin("")
absMoveSelectedCellsToBin("Block")

absDeselectAllBins()

;        absSelectBin("")
absSelectBin("Block")
""")

	f.write("""
;       absSetBinOption("Block" "PinsBoundaryCreate" "as needed")
;absSetBinOption("Block" "PinsBoundaryCreate" "always")
;absSetBinOption("Block" "PinsBoundaryLayers" "prBoundary")

absSetBinOption("Block" "ExtractSig" "false")
absSetBinOption("Block" "ExtractPwr" "false")
absSetBinOption("Block" "ExtractConnectivity" "")

absSetBinOption("Block" "AbstractAdjustBoundaryPinsSig" "true")
absSetBinOption("Block" "AbstractAdjustBoundaryPinsPwr" "false")
absSetBinOption("Block" "AbstractAdjustBoundaryPinsSigDist" "1")
absSetBinOption("Block" "AbstractAdjustBoundaryPinsPwrDist" "0")
absSetBinOption("Block" "AbstractAdjustRingPinsPwr" "false")
absSetBinOption("Block" "AbstractAdjustFollowRingPin" "false")
absSetBinOption("Block" "AbstractAdjustPowerGeometryGroups" "overlap")
absSetBinOption("Block" "AbstractAdjustEdgeTowardsCore" "north")
absSetBinOption("Block" "AbstractAdjustClassCoreNets" "")
absSetBinOption("Block" "AbstractAdjustIncludeAllShapes" "false")
absSetBinOption("Block" "AbstractAdjustCopyClassCorePort" "false")
absSetBinOption("Block" "AbstractAdjustPinsTouchBoundary" "false")
absSetBinOption("Block" "AbstractAdjustStairStepCover" "full")
absSetBinOption("Block" "AbstractAdjustStairStepWidth" "0.12")
absSetBinOption("Block" "AbstractBlockageTable" "")
absSetBinOption("Block" "AbstractBlockageCoverLayers" "")
absSetBinOption("Block" "AbstractBlockageDetailedLayers" "")
absSetBinOption("Block" "AbstractBlockageCoverLayersDist" "")
absSetBinOption("Block" "AbstractBlockageFracture" "true")
absSetBinOption("Block" "AbstractOverlapLayerAction" "off")
absSetBinOption("Block" "AbstractOverlapLayers" "")
absSetBinOption("Block" "AbstractOverlapLayerSize" "0")
absSetBinOption("Block" "AbstractOverlapLayerSmoothFactor" "15")
absSetBinOption("Block" "AbstractPinFracture" "true")
absSetBinOption("Block" "AbstractBlockageModelWideObs" "false")
absSetBinOption("Block" "AbstractGridMode" "off")
absSetBinOption("Block" "AbstractRetainLayout" "true")
absSetBinOption("Block" "AbstractSiteName" "")
absSetBinOption("Block" "AbstractSiteNameDefine" "")
""")

	for bin_name,opts in self.abstract_options.iteritems():
		for key,value in opts.iteritems():
			f.write('absSetBinOption( "'+bin_name+'" "'+key+'" "'+value+'")\n')

	if hasattr(self,'termprops'):
		for cell, opts in self.termprops.iteritems():
			for pin, props in opts.iteritems():
				f.write('absSetTerminalProp( "'+cell+'" "'+pin+'" "'+('" "'.join(props))+'")\n')

	if export_lef_file:
		f.write("""
absSetOption("ExportLEFVersion" 	"5.5")
absSetOption("ExportGeometryLefData" 	"true")
absSetOption("ExportTechLefData" 	"false")
absSetOption("ExportLEFBin" 		"Block")
absSetOption("ExportLEFFile" 		"{0}")
""".format(export_lef_file.abspath()))

	f.write("""
absPins()
absExtract()
absAbstract()

absSetCellProp("{0}" "symmetry" "X Y R90")
""".format(self.cellname))

	if export_lef_file:
		f.write("""
absExportLEF()
""")

	f.write("""
absExit()
""".format())

	f.close()

	inputs = [input_layout_node]
	outputs = []
	if export_lef_file:
		outputs.append(export_lef_file)

	t = self.create_task('cdsAbsgenTask',inputs,outputs)

class cdsAbsgenTask(Task.Task):
	vars = ['CADENCE_ABSTRACT','CADENCE_ABSTRACT_OPTIONS']

	def run(self):
		run_str = 'cd %s && %s %s -replay %s 2>&1' % (self.generator.path.get_bld().abspath(), self.env.CADENCE_ABSTRACT, " ".join(self.env.CADENCE_ABSTRACT_OPTIONS), self.generator.absgen_script.abspath())
		out = ""
		try:
			out = self.generator.bld.cmd_and_log(run_str)#, quiet=Context.STDOUT)
		except Exception as e:
			out = e.stdout

		logfile = self.generator.path.get_bld().make_node(os.path.join(self.generator.path.bld_dir(),self.env.BRICK_LOGFILES,'abstract_'+self.generator.libname+'_'+self.generator.cellname+'.log'))
		f = open(logfile.abspath(),'w')
		f.write(out)
		f.close()

		return 0




@TaskGen.feature('cadence_absgen_blabb')
def blubb(self):

	self.liberate_script = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'liberate_script_'+self.cell+'.tcl'))

	if not getattr(self,'netlists_spice',None):
		self.netlists_spice = []
	if not getattr(self,'netlists_spectre',None):
		self.netlists_spectre = []

	netlists_strings_spice = []
	for netlist in getattr(self,'netlists_spice',[]):
		#if not netlist:
		#	Logs.error('You have given an undefined node object as netlist for feature "altos_liberate".')
		#	return
		try:
			netlists_strings_spice.append(netlist.abspath())
		except AttributeError:
			netlists_strings_spice.append(netlist)

	netlists_strings_spectre = []
	for netlist in getattr(self,'netlists_spectre',[]):
		#if not netlist:
		#	Logs.error('You have given an undefined node object as netlist for feature "altos_liberate".')
		#	return
		try:
			netlists_strings_spectre.append(netlist.abspath())
		except AttributeError:
			netlists_strings_spectre.append(netlist)


	output_library = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),self.env.BRICK_RESULTS,self.cell+'.lib'))

	f = open(self.liberate_script.abspath(),"w")
	try:
		tcl_string = """
# Define templates for characterization.
# Delay template for 3 input slews and 3 loads
define_template -type constraint \\
    -index_1 {{0.0001 0.0002 0.0003}} \\
    -index_2 {{0.0001 0.0002 0.0003}} \\
    constraint_3x3

define_template -type delay \\
    -index_1 {{0.026973 0.047707 0.103269 0.334201 0.800188 1.965635}} \\
    -index_2 {{0.002000 0.006100 0.018607 0.056753 0.173106 0.528000}} \\
    delay_6x6

define_template -type delay \\
    -index_1 {{0.0001 0.0002 0.0003 0.0004 0.0005 0.0006 0.0007}} \\
    -index_2 {{0.0001 0.0002 0.0003 0.0004 0.0005 0.0006 0.0007}} \\
    delay_7x7_0

# Power template for 3 input slews and 3 loads
define_template -type power \\
    -index_1 {{0.026968 0.047707 0.103268 0.334201 0.800117 1.965723}} \\
    -index_2 {{0.002000 0.006100 0.018607 0.056753 0.173106 0.528000}} \\
    power_6x6

define_template -type power \\
    -index_1 {{0.0001 0.0002 0.0003 0.0004 0.0005 0.0006 0.0007}} \\
    -index_2 {{0.0001 0.0002 0.0003 0.0004 0.0005 0.0006 0.0007}} \\
    power_7x7_0

# Specify the PVT for this characterization run
set_operating_condition -voltage 1.2 -temp 25

#set_var measure_slew_lower_fall 0.1
#set_var measure_slew_upper_fall 0.9
#set_var measure_slew_lower_rise 0.1
#set_var measure_slew_upper_rise 0.9
#
#set_units -leakage_power 1pw
""".format()
		if netlists_strings_spice:
			tcl_string += """
read_spice -format hspice {{ \\
	{0} \\
}}
""".format(' \\\n\t'.join(netlists_strings_spice))
		if netlists_strings_spectre:
			tcl_string += """
read_spice -format spectre {{ \\
	{0} \\
}}
""".format(' \\\n\t'.join(netlists_strings_spectre))
		tcl_string += """
set_vdd vdd 1.2
set_vdd vdd12a 1.2
set_vdd vdd12d 1.2
set_gnd gnd 0
set_gnd gndd 0
set_gnd gnda 0

define_cell \\
    -input {{ {0} }} \\
    -output {{ {1} }} \\
    -clock {{ {2} }} \\
    -bidi {{ {3} }} \\
    -delay delay_7x7_0 \\
    -power power_7x7_0 \\
    -constraint constraint_3x3 \\
	-pinlist {{ {0} {1} {2} {3} }} \\
    {{ {4} }}

""".format(
				' '.join(getattr(self,'input',[])),
				" ".join(getattr(self,'output',[])),
				" ".join(getattr(self,'clock',[])),
				" ".join(getattr(self,'bidi',[])),
				self.cell,
			)
	except AttributeError:
		Logs.error('Please define a cell name with parameter "cell" for feature "altos_liberate".')

	if hasattr(self,'arcs'):
		tcl_string += " \n".join(self.arcs)
		tcl_string += "\n"

	tcl_string += "char_library -skip {leakage power mpw delay}"
	if hasattr(self,'io_only') and getattr(self,'io_only',False) == True:
		tcl_string += ' -io'
	if hasattr(self,'user_arcs_only') and getattr(self,'user_arcs_only',False) == True:
		tcl_string += ' -user_arcs_only'

	tcl_string += "\nwrite_library -overwrite {0}\n".format(output_library.abspath())

	f.write(tcl_string)
	f.close()

	t = self.create_task('altosLibTask', self.netlists_spice+self.netlists_spectre, output_library)

# vim: noexpandtab:
