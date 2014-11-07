import os,re
from brick_general import ChattyBrickTask
from waflib import Task,Errors,Node,TaskGen,Configure,Context,Logs

def configure(conf):
	"""This function gets called by waf upon loading of this module in a configure method"""

	conf.load('brick_general')


	conf.find_program('abstract', var='CADENCE_ABSTRACT')
	conf.env['CADENCE_ABSTRACT_OPTIONS'] = [
			'-nogui',
		]


@TaskGen.feature('cds_absgen')
def create_cadence_absgen_task(self):

    # extract lib, cell and view
	libname,cellname,viewname = self.get_cadence_lib_cell_view_from_cellview()

	# prepare nodes for script, layout and lef file
	self.absgen_script = self.bld.bldnode.make_node('absgen_'+libname+'_'+cellname+'_'+viewname+'.il')
	input_layout_node = self.get_cellview_path(self.cellview).find_node('layout.oa')

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

			"PinsBoundaryLayers": "M1 M2 M3 M4 M5 M6 M7 M8 M9 prBoundary",
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
""".format(libname,cellname))

	f.write("""
;        absMoveSelectedCellsToBin("")
absMoveSelectedCellsToBin("Block")

absDeselectAllBins()

absSelectBin("Block")
absSelectCell("{0}")
""".format(cellname))

	# LEF export options
	if not getattr(self,'dont_export_lef_file',False):
		f.write("""
absSetOption("ExportLEFVersion" 	"5.5")
absSetOption("ExportGeometryLefData" 	"true")
absSetOption("ExportTechLefData" 	"false")
absSetOption("ExportLEFBin" 		"Block")
absSetOption("ExportLEFFile" 		"{0}")
""".format(self.get_cadence_absgen_result_node().abspath()))

	# Block bin options
	f.write("""
;       absSetBinOption("Block" "PinsBoundaryCreate" "as needed")
absSetBinOption("Block" "PinsBoundaryCreate" "always")

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
absSetBinOption("Block" "AbstractOverlapLayerSize" "0")
absSetBinOption("Block" "AbstractOverlapLayerSmoothFactor" "15")
absSetBinOption("Block" "AbstractPinFracture" "true")
absSetBinOption("Block" "AbstractBlockageModelWideObs" "false")
absSetBinOption("Block" "AbstractGridMode" "off")
absSetBinOption("Block" "AbstractRetainLayout" "true")
absSetBinOption("Block" "AbstractSiteName" "")
absSetBinOption("Block" "AbstractSiteNameDefine" "")
""")

	# user-defined options
	for bin_name,opts in self.abstract_options.iteritems():
		for key,value in opts.iteritems():
			f.write('absSetBinOption( "'+bin_name+'" "'+key+'" "'+value+'")\n')

	f.write("""
absSetOption("ViewLayout" "{0}")
absPins()
absExtract()
absAbstract()

absSetCellProp("{1}" "symmetry" "X Y R90")
""".format(viewname,cellname))

	if hasattr(self,'termprops'):
		for pin, props in self.termprops.iteritems():
			f.write('absSetTerminalProp( "'+cellname+'" "'+pin+'" "'+('" "'.join(props))+'")\n')

	if not getattr(self,'dont_export_lef_file',False):
		f.write("""
absExportLEF()
""")

	f.write("""
absExit()
""".format())

	f.close()

	inputs = [input_layout_node]
	outputs = []
	if hasattr(self,'export_lef_file'):
		outputs.append(self.export_lef_file)
	else:
		outputs.append(self.get_cadence_absgen_result_node())

	t = self.create_task('cdsAbsgenTask',inputs,outputs)


@TaskGen.taskgen_method
def get_cadence_absgen_logfile_node(self):
	libname,cellname,viewname = self.get_cadence_lib_cell_view_from_cellview()
	return self.get_logdir_node().make_node('abstract_'+libname+'_'+cellname+'.log')

@TaskGen.taskgen_method
def get_cadence_absgen_result_node(self):
	if hasattr(self,'export_lef_file'):
		return self.export_lef_file
	else:
		results_dir = self.bld.bldnode.find_node('results')
		lib,cell,view = self.get_cadence_lib_cell_view_from_cellview()
		return results_dir.make_node(lib+'_'+cell+'.lef')


class cdsAbsgenTask(ChattyBrickTask):
	vars = ['CADENCE_ABSTRACT','CADENCE_ABSTRACT_OPTIONS']
	run_str = '${env.CADENCE_ABSTRACT} ${env.CADENCE_ABSTRACT_OPTIONS} -replay ${gen.absgen_script.abspath()} -log ${gen.get_cadence_absgen_logfile_node().abspath()}'


	def check_output(self,ret,out):
		for num,line in enumerate(out.split('\n')):
			if line.find('*Error*')>=0 or line.find('ERROR')==0:
				Logs.error("Error in line %d: %s" % (num,line))
				ret = 1

		return ret



# vim: noexpandtab:
