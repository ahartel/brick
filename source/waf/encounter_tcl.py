flow_settings_tcl = """
###################################################################################################
#
# Flow Setup
#

#
# Enabling this prevents place step from generating a CTS spec
#
set use_external_cts_spec   {0}

#
# Save and load design with def files, skip OA mode
#
set use_lef_flow            {1}

#
# In case of chip toplevel, enable IO fill during floorplan step
#
set enable_iofill           {2}

#
# Enable core fill during final step
#
set enable_corefill         {3}

#
# Load saved floorplan
#
set enable_load_floorplan   {4}

#
# Define hold and setup target slacks (prects/postcts/postroute steps)
#
set target_hold_slack       {5}
set target_setup_slack      {6}
set drc_margin_factor       {7}

#
# Enable enable metal fill (final step)
#
set enable_metalfill        {8}

#
# Enable Fire & Ice QX Extraction
#
set enable_qx               {9}

#
# Enable RC factor generation for better result matching (Fire & Ice QX Extraction required)
#
set enable_rcgen            {10}

#
# Enable Crosstalk fixing using CeltIC (Fire & Ice QX Extraction required)
#
set enable_si               {11}

#
# Enable Usefulskew optimization
#
set enable_usefulskew       {12}

#
# Enable On Chip Variation (OCV) timing analysis (postroute step, preliminary flow!)
#
set enable_ocv              {13}

#
# Power Analysis Setup
#
set supply_voltage        "1.2"
# Choose index for power net name from list $pwrnet
set pwrnetindex           0
# Choose temperature for power analysis
set temperature           85
# Define type of power analysis ("statistical", "postCTS" or "vcd" )
set power_ana_type        "statistical"
# Choose, which rail analysis results you want to see ("irdrop" or "em")
set rail_ana_type         "irdrop"
# VCD file
set vcd_file              "<YOUR INPUT>"
# VCD scope
set vcd_scope             "<YOUR INPUT>"

#
# ECO Setup
#
set previous_version      ""
set version               ""
"""

corner_def_tcl = """
########################################

create_library_set \\
	-name WORST_LIBSET \\
	-timing [list $max_timing_lib ]

create_rc_corner \\
	-name RCWORST \\
	-cap_table $cap_table_max \\
	-T 125 \\
	-qx_tech_file $qx_tech_file_rcworst

create_delay_corner \\
	-name MAX_CORNER \\
	-library_set WORST_LIBSET \\
	-opcond_library {0} \\
	-opcond {1} \\
	-rc_corner RCWORST

########################################

create_library_set \\
	-name BEST_LIBSET \\
	-timing  [list $min_timing_lib ]

create_rc_corner \\
	-name RCBEST \\
	-cap_table $cap_table_min \\
	-T 0 \\
	-qx_tech_file $qx_tech_file_rcbest

create_delay_corner \\
	-name MIN_CORNER \\
	-library_set BEST_LIBSET \\
	-opcond_library {2} \\
	-opcond {3} \\
	-rc_corner RCBEST

########################################

create_library_set \\
	-name TYP_LIBSET \\
        -timing [list $typ_timing_lib]

create_rc_corner \\
	-name RCTYP \\
	-cap_table $cap_table_typ \\
	-T 27 \\
	-qx_tech_file $qx_tech_file_rctyp

create_delay_corner \\
	-name TYP_CORNER \\
	-library_set TYP_LIBSET \\
	-opcond_library {4} \\
	-opcond {5} \\
	-rc_corner RCTYP

########################################

create_constraint_mode \\
	-name missionSetup \\
	-sdc_files $con_files

########################################

create_analysis_view \\
	-name missionSlow \\
	-delay_corner MAX_CORNER \\
	-constraint_mode missionSetup

create_analysis_view \\
	-name missionTyp \\
	-delay_corner TYP_CORNER \\
	-constraint_mode missionSetup

create_analysis_view \\
	-name missionFast \\
	-delay_corner MIN_CORNER \\
	-constraint_mode missionSetup

########################################	

set_analysis_view \\
	-setup {{missionSlow missionTyp}} \\
	-hold {{missionFast missionTyp}}
"""

setup_tcl = """
set BRICK_RESULTS [getenv "BRICK_RESULTS"]

setMultiCpuUsage -localCpu 8

#
# Design
#
set toplevel               "{0}"
set netlist                "{1}"
set con_files              "{2}"
set io_placement_file      "{3}"
set tool                   "encounter"

set enc_save_oalib			"encounter_oa"

#
# Encounter Setup
#

set lef_files              [list "{4}"]


set max_timing_lib         [list "{5}"]
set typ_timing_lib         [list "{6}"]
set min_timing_lib         [list "{7}"]



###################################################################################################

set cap_table_typ          "{8}"
set cap_table_max          "{9}"
set cap_table_min          "{10}"

set stream_out_map         "{11}"

set pwrnet                 "vdd12d vdd25a vdd12a vdd25d"

set gndnet					"gndd gnda"

set buf_footprint          "buffd1"

set delay_footprint        "del1"

set inv_footprint          "invd1"

set clk_buffer_list        "CKBD1 CKBD2 CKBD3 CKBD4 CKBD6 CKBD8 CKBD12 CKBD16 "

set core_filler_list       "DCAP64 DCAP32 DCAP16 DCAP8 DCAP4 DCAP FILL64 FILL32 FILL16 FILL8 FILL4 FILL2 FILL1"

set io_filler_list         "PFILLER20A PFILLER10A PFILLER5A PFILLER1A PFILLER05A PFILLER0005A"
set io_filler_list_dig     "PFILLER20  PFILLER10  PFILLER5  PFILLER1  PFILLER05  PFILLER0005"

set lvs_phy_cells          "DCAP64 DCAP32 DCAP16 DCAP8 DCAP4 DCAP FILL64 FILL32 FILL16 FILL8 FILL4 FILL2 FILL1 PVDD1ANA PVDD1CDG PVDD2CDG PVDD2POC PVDD3A PVDD3AC PVSS1CDG PVSS2A PVSS2CDG PVSS3A PVSS3AC"

set ant_cells              "ANTENNA"

set metal_layer            "M1 M2 M3 M4 M5 M6 M7 M8 M9"

#
# CeltIC Setup
#
set max_noise_lib          ""

set typ_noise_lib          ""

set min_noise_lib          ""

set noise_process          "65"

#
# Fire and Ice Setup
#
set qx_tech_file_rctyp         "{12}"
set qx_tech_file_rcworst       "{13}"
set qx_tech_file_rcbest        "{14}"
set qx_leflayer_map            "{15}"



###################################################################################################
#
# Flow Setup
#
source {16}
"""

steps_tcl = {}
steps_tcl['bind'] = """
#
# 1. Import and check synthesis results
# 2. Bind netlist to technology
# 3. Save imported design
#

setLicenseCheck -status -existOnServer

source {0}

setDesignMode -process $noise_process

######REPLACEMENT WITH init_design FLOW

set init_import_mode "-treatUndefinedCellAsBbox 0 -keepEmptyModule 1 "
set defHierChar {{/}}

#Set Verilog Netlist
set init_verilog $netlist

set init_design_settop 0

######################################################
# LEF File
# Enabling set init_lef_file will prevent encounter
# from reading the oa libs
#########################################################
if {{$use_lef_flow}} {{
	#setImportMode -useLefDef56 1
	set init_lef_file $lef_files
}}

set init_design_netlisttype "Verilog"
set init_assign_buffer 1

set init_pwr_net $pwrnet
set init_gnd_net $gndnet


#TIMINIG CONSTRAINTS, SDC AND CAPACITANCE INFORMATIONS HAVE MOVED TO THE MMMC CONFIGURATION FILES
set init_mmmc_file {1}


#OA Libraries
#OPENACCESS Configuration
if {{!$use_lef_flow}} {{
	#set locv_inter_clock_use_worst_derate false
	set init_oa_ref_lib {{{2}}}
	set init_oa_search_lib {{{3}}}
	# this is the default value, anyway
	set init_abstract_view {{abstract}}
	set init_layout_view {{layout}}
}}

# don't know what this means, couldn't find hint in the official documentation
#set lsgOCPGainMult 1.000000

#set delaycal_input_transition_delay {{0.1ps}}
#set conf_qxconf_file {{NULL}}
#set conf_qxlib_file {{NULL}}
#set fpIsMaxIoHeight 0
#set timing_case_analysis_for_icg_propagation false


setOaxMode -compressLevel 0
setOaxMode -displayDrfFile "./display.drf"
setOaxMode -useVirtuosoColor {{true}}

init_design

#
#check timing of synthesized netlist
#
timeDesign -prePlace -outDir ./reports

if {{$version != ""}} {{
	if {{!$use_lef_flow}} {{
		saveDesign -cellview "${{enc_save_oalib}} ${{toplevel}}_bind_$version layout"
	}} else {{
		saveDesign $BRICK_RESULTS/$toplevel\_enc/$toplevel\__bind_$version.enc -def
	}}
}} else {{
	if {{!$use_lef_flow}} {{
		saveDesign -cellview "${{enc_save_oalib}} ${{toplevel}}_bind layout"
	}} else {{
		saveDesign $BRICK_RESULTS/$toplevel\_enc/$toplevel\_bind.enc -def
	}}
}}

exit
"""

steps_tcl['floorplan'] = """
#
# Import Bind Step Encounter DB 
#
source {0}
source {1}

if {{$version != ""}} {{
	if {{$use_lef_flow}} {{
		restoreDesign $BRICK_RESULTS/$toplevel\_enc/$toplevel\_bind_$version.enc.dat $toplevel
	}} else {{
		restoreDesign -cellview "${{enc_save_oalib}} ${{toplevel}}_bind_$version layout"
	}}
}} else {{
	if {{$use_lef_flow}} {{
		restoreDesign $BRICK_RESULTS/$toplevel\_enc/$toplevel\_bind.enc.dat $toplevel
	}} else {{
		restoreDesign -cellview "${{enc_save_oalib}} ${{toplevel}}_bind layout"
	}}
}}

#  
# Init floorplan
#

if {{$enable_load_floorplan == 0}} {{
    #
    # specify Floorplan
    #
	# order of parameters:
	# die_x1 die_y1 die_x2 die_y2 io_x1 io_y1 io_x2 io_y2 core_x1 core_y1 core_x2 core_y2
    floorPlan -site core -b $xofset $yofset \
				$top_pins_w $top_pins_h \
				[expr ($xofset + $h_pad)] [expr ($yofset + $h_pad)] \
				[expr ($top_pins_w - $h_pad)] [expr ($top_pins_h - $h_pad)] \
				[expr ($xofset + $h_pad + $top_pins_ctl)] [expr ($yofset + $h_pad + $top_pins_ctb)] \
				[expr ($top_pins_w - $h_pad - $top_pins_ctr)] [expr ($top_pins_h - $h_pad - $top_pins_ctt)]

    loadIoFile $io_placement_file -noAdjustDieSize
}} else {{
#    # alternatively save and load floor plan 
#    # typically the floorplan is initialized once as above, then the IO shifted
#    # around properly using the GUI and the floorplan saved. Then only the floorplan
#    # should be loaded as the io file automatically scales and shifts the objects.
    loadFPlan ./scripts/$toplevel\_fp.tcl
}}

#
# place hard macros bloks, make routing blokiges arriund them
# Route Power
#

if {{{2}}} {{
    source {3}
}}

##Save new netlist
saveNetlist $BRICK_RESULTS/$toplevel.save.v
saveNetlist $BRICK_RESULTS/$toplevel.save.phys.v -includePhysicalInst -includePowerGround

#
# Add IO filler cells:
#
if {{$enable_iofill}} {{
    set io_fill_count [llength $io_filler_list]

    # Start with biggest, fill any gap with smallest
    for {{set i 0}} {{$i<$io_fill_count}} {{incr i}} {{
        if {{$i==[expr $io_fill_count-1]}} {{
            addIoFiller -cell [lindex $io_filler_list $i] -prefix iofill -fillAnyGap
        }} else {{
            addIoFiller -cell [lindex $io_filler_list $i] -prefix iofill
        }}
    }}
}}


#Save Floorplan in Encounter DB

if {{$version != ""}} {{
	if {{$use_lef_flow}} {{
		saveDesign $BRICK_RESULTS/$toplevel\_enc/$toplevel\_floorplan_$version.enc -def
	}} else {{
		saveDesign -cellview "${{enc_save_oalib}} ${{toplevel}}_floorplan_$version layout"
	}}
    # Save Floorplan file specal format
    saveFPlan  $BRICK_RESULTS/$toplevel\_enc/$toplevel\_floorplan_$version.fp
}} else {{
	if {{$use_lef_flow}} {{
		saveDesign $BRICK_RESULTS/$toplevel\_enc/$toplevel\_floorplan.enc -def
	}} else {{
		saveDesign -cellview "${{enc_save_oalib}} ${{toplevel}}_floorplan layout"
	}}
    # Save Floorplan file specal format
    saveFPlan  $BRICK_RESULTS/$toplevel\_enc/$toplevel\_floorplan.fp
}}

exit
"""

steps_tcl['place'] = """
#
# Import Floorplan Step Encounter DB
#
source {0}

if {{$version != ""}} {{
	if {{$use_lef_flow}} {{
		restoreDesign $BRICK_RESULTS/$toplevel\_enc/$toplevel\_floorplan_$version.enc.dat $toplevel
	}} else {{
		restoreDesign -cellview "${{enc_save_oalib}} ${{toplevel}}_floorplan_$version layout"
	}}
}} else {{
	if {{$use_lef_flow}} {{
		restoreDesign $BRICK_RESULTS/$toplevel\_enc/$toplevel\_floorplan.enc.dat $toplevel
	}} else {{
		restoreDesign -cellview "${{enc_save_oalib}} ${{toplevel}}_floorplan layout"
	}}
}}

source {1}

if {{{2}}} {{
    source {3}
}}

#
# Start STD-Cell Placement
#

#clock tree specification file is needed for clock gate awareness placement, based on synthesis sdc
if {{$use_external_cts_spec == 0}} {{
    createClockTreeSpec -bufferList $clk_buffer_list -output ./scripts/$toplevel.cts.spec
}}
specifyClockTree -file ./scripts/$toplevel.cts.spec


#
# Place Std-Cells
#
setPlaceMode -placeIoPins true -clkGateAware true -congEffort high \
             -honorSoftBlockage true -maxRouteLayer [llength $metal_layer] \
             -maxDensity 0.7 -modulePlan true -timingDriven true \
             -padForPinNearBorder true

placeDesign


#
# Enable spare cell insertion
#
if {{0}} {{
	source ./scripts/$toplevel.spare_cells.tcl
}}


# Run Trail Route (fast)
# to determine early whether or not we have good placement
trialRoute

checkPlace

#
# Save Place Encounter DB
#
if {{$version != ""}} {{
	if {{$use_lef_flow}} {{
		saveDesign $BRICK_RESULTS/$toplevel\_enc/$toplevel\_place_$version.enc -def
	}} else {{
		saveDesign -cellview "${{enc_save_oalib}} ${{toplevel}}_place_$version layout"
	}}
}} else {{
	if {{$use_lef_flow}} {{
		saveDesign $BRICK_RESULTS/$toplevel\_enc/$toplevel\_place.enc -def
	}} else {{
		saveDesign -cellview "${{enc_save_oalib}} ${{toplevel}}_place layout"
	}}
}}

exit

"""
