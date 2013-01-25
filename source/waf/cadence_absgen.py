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

	self.absgen_script = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'absgen_'+self.libname+'_'+self.cellname+'.il'))

	input_layout_file = self.get_cellview_path(cellview).find_node('layout.oa').abspath()

	export_lef_file = getattr(self,'export_lef_file',None)

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

absSetBinOption( "Block" "AbstractBlockageShrinkWrapLayers" "{0}")
absSetBinOption( "Block" "AbstractBlockageShrinkAdjust" "{1}")
absSetBinOption( "Block" "AbstractBlockageCoverLayers" "{2}")
absSetBinOption( "Block" "AbstractBlockageCoverLayersDist" "{3}")
	
absSetBinOption( "Block" "AbstractBlockagePinCutWindow" "{4}" )
absSetBinOption( "Block" "AbstractBlockageDownPinCutWindow" "{5}")
absSetBinOption( "Block" "AbstractBlockageCutAroundPin" "{6}")

absSetBinOption( "Block" "AbstractBlockageDetailedLayers"       "{7}")

absSetBinOption( "Block" "PinsPowerNames"        "{8}")
absSetBinOption( "Block" "PinsGroundNames"       "{9}")
absSetBinOption( "Block" "PinsClockNames"        "{10}")
absSetBinOption( "Block" "PinsAnalogNames"       "{11}")
absSetBinOption( "Block" "PinsOutputNames"       "{12}")
absSetBinOption( "Block" "PinsTextPinMap"        "{13}" ) 
absSetBinOption( "Block" "ExtractConnectivity"   "{14}")
""".format(
		getattr(self,'abstract_blockage_shrink_wrap_layers',""),
		getattr(self,'abstract_blockage_shrink_adjust',""),
		getattr(self,'abstract_blockage_cover_layers',""),
		getattr(self,'abstract_blockage_cover_layers_dist',""),

		getattr(self,'abstract_blockage_pincutwindow',''),
		getattr(self,'abstract_blockage_down_pincutwindow',''),
		getattr(self,'abstract_blockage_cutaroundpin',''),
		getattr(self,'abstract_blockage_detailed_layers',''),

		getattr(self,'pins_power_names',''),
		getattr(self,'pins_ground_names',''),
		getattr(self,'pins_clock_names',''),
		getattr(self,'pins_analog_names',''),
		getattr(self,'pins_output_names',''),
		getattr(self,'pins_textpinmap',''),
		getattr(self,'extract_connectivity',''),
		))

	if export_lef_file:
		f.write("""
absSetOption("ExportLEFVersion" 	"5.5")
absSetOption("ExportGeometryLefData" 	"true")
absSetOption("ExportTechLefData" 	"false")
absSetOption("ExportLEFBin" 		"Block")
absSetOption("ExportLEFFile" 		"{0}")
""".format())

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

	t = self.create_task('cdsAbsgenTask')# input_layout_file, )

class cdsAbsgenTask(Task.Task):
	vars = ['CADENCE_ABSTRACT','CADENCE_ABSTRACT_OPTIONS']

	def run(self):
		run_str = 'cd build && %s %s -replay %s 2>&1' % (self.env.CADENCE_ABSTRACT, " ".join(self.env.CADENCE_ABSTRACT_OPTIONS), self.generator.absgen_script.abspath())
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
