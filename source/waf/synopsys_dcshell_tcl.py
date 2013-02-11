
dc_shell_setup_tcl = {
############
# default
############
'default': """
set BRICK_RESULTS				[getenv "BRICK_RESULTS"]; 
set TSMC_DIR                    [getenv "TSMC_DIR"]; 

set DESIGN_NAME                 "%s";      # The name of the top-level design.

#############################################################
# The following variables will be set automatically during
# 'icdc setup' -> 'commit setup' execution
# Manual changes could be made, but will be overwritten 
# when 'icdc setup' is executed again
#
##############################################################
# START Auto Setup Section

# Additional search path to be added
# to the default search path
# The search paths belong to the following libraries:
# * core standard cell library
# * analog I/O standard cell library
# * digital I/O standard cell library
# * SRAM macro library
# * full custom macro libraries
set ADDITIONAL_SEARCH_PATHS	[list \\
    %s
]

# Target technology logical libraries                    							
set TARGET_LIBRARY_FILES	[list \\
]

# List of max min library pairs "max1 min1  max2 min2"
set MIN_LIBRARY_FILES	[list \\
]

# END Auto Setup Section        
##############################################################

# Extra link logical libraries
set ADDITIONAL_LINK_LIB_FILES [list \\
    %s
]


##############################################################
# Topo Mode Settings
# no auto setup implemented so far
# please make necessary modification
#
set MW_REFERENCE_LIB_DIRS         "";             # Milkyway reference libraries
set TECH_FILE                     "";  			# Milkyway technology file
set MAP_FILE                      ""; 			# Mapping file for TLUplus
set TLUPLUS_MAX_FILE              "";          	# Max TLUplus file
set TLUPLUS_MIN_FILE              "";         	# Min TLUplus file
set MW_POWER_NET                  "";     		#
set MW_POWER_PORT                 "";      	    #
set MW_GROUND_NET                 "";      	    #
set MW_GROUND_PORT                "";      	    #
""",
#############
# TSMC65
#############
'tsmc65': """
set BRICK_RESULTS				[getenv "BRICK_RESULTS"]; 
set TSMC_DIR                    [getenv "TSMC_DIR"]; 

set DESIGN_NAME                 "%s";      # The name of the top-level design.

#############################################################
# The following variables will be set automatically during
# 'icdc setup' -> 'commit setup' execution
# Manual changes could be made, but will be overwritten 
# when 'icdc setup' is executed again
#
##############################################################
# START Auto Setup Section

# Additional search path to be added
# to the default search path
# The search paths belong to the following libraries:
# * core standard cell library
# * analog I/O standard cell library
# * digital I/O standard cell library
# * SRAM macro library
# * full custom macro libraries
set ADDITIONAL_SEARCH_PATHS	[list \\
    "$TSMC_DIR/digital/Front_End/timing_power_noise/NLDM/tcbn65lp_200a" \\
    "$TSMC_DIR/digital/Front_End/timing_power_noise/NLDM/tpan65lpnv2_140b" \\
    "$TSMC_DIR/digital/Front_End/timing_power_noise/NLDM/tpdn65lpnv2_140b" \\
    "$TSMC_DIR/sram/tsdn65lpa4096x32m8f_200b/SYNOPSYS" \\
    %s
]

# Target technology logical libraries                    							
set TARGET_LIBRARY_FILES	[list \\
    "tcbn65lpwc.db" \\
    "tcbn65lpwc0d90d9.db" \\
    "tpan65lpnv2wc.db" \\
    "tpdn65lpnv2wc.db" \\
    "tsdn65lpa4096x32m8f_200b_tt1p2v40c.db" \\
]

# List of max min library pairs "max1 min1  max2 min2"
set MIN_LIBRARY_FILES	[list \\
    "tcbn65lpwc.db"    "tcbn65lpbc.db" \\
    "tpan65lpnv2wc.db" "tpan65lpnv2bc.db" \\
    "tpdn65lpnv2wc.db" "tpdn65lpnv2bc.db" \\
]

# END Auto Setup Section        
##############################################################

# Extra link logical libraries
set ADDITIONAL_LINK_LIB_FILES [list \\
    %s
]


##############################################################
# Topo Mode Settings
# no auto setup implemented so far
# please make necessary modification
#
set MW_REFERENCE_LIB_DIRS         "$TSMC_DIR/digital/Back_End/milkyway/tcbn65lp_200a/frame_only/tcbn65lp $TSMC_DIR/digital/Back_End/milkyway/tpdn65lpnv2_140b/mt_2/9lm/frame_only/tpdn65lpnv2 $TSMC_DIR/digital/Back_End/milkyway/tpan65lpnv2_140b/mt_2/9lm/frame_only/tpan65lpnv2";             # Milkyway reference libraries
set TECH_FILE                     "$TSMC_DIR/digital/Back_End/milkyway/tcbn65lp_200a/techfiles/tsmcn65_9lmT2.tf";  			# Milkyway technology file
set MAP_FILE                      "$TSMC_DIR/digital/Back_End/milkyway/tcbn65lp_200a/techfiles/tluplus/star.map_9M"; 			# Mapping file for TLUplus
set TLUPLUS_MAX_FILE              "$TSMC_DIR/digital/Back_End/milkyway/tcbn65lp_200a/techfiles/tluplus/cln65lp_1p09m+alrdl_rcworst_top2.tluplus";          	# Max TLUplus file
set TLUPLUS_MIN_FILE              "$TSMC_DIR/digital/Back_End/milkyway/tcbn65lp_200a/techfiles/tluplus/cln65lp_1p09m+alrdl_rcbest_top2.tluplus";         	# Min TLUplus file
set MW_POWER_NET                  "";     		#
set MW_POWER_PORT                 "";      	    #
set MW_GROUND_NET                 "";      	    #
set MW_GROUND_PORT                "";      	    #


if {[shell_is_in_topographical_mode]} {
	set_preferred_routing_direction -layer M1 -dir horizontal
	set_preferred_routing_direction -layer M2 -dir vertical
	set_preferred_routing_direction -layer M3 -dir horizontal
	set_preferred_routing_direction -layer M4 -dir vertical
	set_preferred_routing_direction -layer M5 -dir horizontal
	set_preferred_routing_direction -layer M6 -dir vertical
	set_preferred_routing_direction -layer M7 -dir horizontal
	set_preferred_routing_direction -layer M8 -dir vertical
	set_preferred_routing_direction -layer M9 -dir horizontal
	set_preferred_routing_direction -layer AP -dir vertical
}
"""
}

dc_shell_main_tcl = """
#
# dc_shell script based on DC-ICPRO
#

# dc_shell_setup.tcl
source %s
# sourcelist
# the following file includes all RTL-Sources as ordered lists
source %s
#########################################################################
# Setup Variables
#########################################################################
#set alib_library_analysis_path $ICPRO_DIR/tmp/dc_shell    ;    # Point to a central cache of analyzed libraries

set clock_gating_enabled 1

# make design read-in a bit more verbose...
#set hdlin_keep_signal_name user
set hdlin_report_floating_net_to_ground true

# Enables shortening of names as the concatenation of interface
# signals results in names > 1000s of characters
set hdlin_shorten_long_module_name true
# Specify minimum number of characters. Default: 256
set hdlin_module_name_limit 100

set DCT_IGNORED_ROUTING_LAYERS     ""     ;    # Enter the same ignored routing
										       # layers as P&R
set REPORTS_DIR                 "$BRICK_RESULTS/dc_shell_$DESIGN_NAME/reports"
set RESULTS_DIR                 "$BRICK_RESULTS/dc_shell_$DESIGN_NAME/results"
set tool                        "dc"

set target_library $TARGET_LIBRARY_FILES
set synthetic_library dw_foundation.sldb
set link_library "* $target_library $ADDITIONAL_LINK_LIB_FILES $synthetic_library"

set search_path [concat  $search_path $ADDITIONAL_SEARCH_PATHS]
# add default icpro search path for global verilog sources
set user_search_path %s
set search_path [concat  $search_path $user_search_path]

# Set min libraries if they exist
foreach {max_library min_library} $MIN_LIBRARY_FILES {
set_min_library $max_library -min_version $min_library }

if {[shell_is_in_topographical_mode]} {
    set mw_logic1_net $MW_POWER_NET
    set mw_logic0_net $MW_GROUND_NET
    set mw_reference_library $MW_REFERENCE_LIB_DIRS
    set mw_design_library ${DESIGN_NAME}_LIB
    set mw_site_name_mapping [list CORE unit Core unit core unit]
    create_mw_lib     -technology $TECH_FILE \
                      -mw_reference_library $mw_reference_library \
                      $mw_design_library
    open_mw_lib       $mw_design_library
    set_tlu_plus_files     -max_tluplus $TLUPLUS_MAX_FILE \
						   -min_tluplus $TLUPLUS_MIN_FILE \
						   -tech2itf_map $MAP_FILE
    check_tlu_plus_files

    check_library
}


## set multicore usage
set_host_options -max_cores 8


echo "Information: Starting Synopsys Design Compiler synthesis run ... "
echo "Information: Filtered command line output. For details see 'logfiles/compile.log'! "

#################################################################################
# Setup for Formality verification
#################################################################################
set_svf $RESULTS_DIR/${DESIGN_NAME}.svf


#################################################################################
# Read in the RTL Design
#
# Read in the RTL source files or read in the elaborated design (DDC).
#################################################################################
define_design_lib WORK -path ./worklib

if { [llength $verilog_source_list] } {
    echo "Information: Analyzing Verilog sources ... "
    analyze -format verilog $verilog_source_list
}

if { [llength $vhdl_source_list] } {
    echo "Information: Analyzing VHDL sources ... "
    analyze -format vhdl $vhdl_source_list
}

if { [llength $systemverilog_source_list] } {
    echo "Information: Analyzing SystemVerilog sources ... "
    analyze -format sverilog $systemverilog_source_list
}

echo "Information: Elaborating top-level '$DESIGN_NAME' ... "
elaborate $DESIGN_NAME


write -format ddc -hierarchy -output $RESULTS_DIR/${DESIGN_NAME}.elab.ddc

list_designs -show_file > $REPORTS_DIR/$DESIGN_NAME.elab.list_designs
report_reference -hier > $REPORTS_DIR/$DESIGN_NAME.elab.report_reference


echo "Information: Linking design ... "
link > $REPORTS_DIR/$DESIGN_NAME.link


############################################################################
# Apply Logical Design Constraints
############################################################################
echo "Information: Reading design constraints ... "
set constraints_file %s
if {$constraints_file != 0} {
    source -echo -verbose ${constraints_file}
}

# Enable area optimization in all flows
set_max_area 0

############################################################################
# Create Default Path Groups
# Remove these path group settings if user path groups already defined
############################################################################
set ports_clock_root [get_ports [all_fanout -flat -clock_tree -level 0]]
group_path -name REGOUT -to [all_outputs]
group_path -name REGIN -from [remove_from_collection [all_inputs] $ports_clock_root]
group_path -name FEEDTHROUGH -from [remove_from_collection [all_inputs] $ports_clock_root] -to [all_outputs]

#################################################################################
# Power Optimization Section
#################################################################################

if ($clock_gating_enabled) {
	set_clock_gating_style \
		-positive_edge_logic integrated \
		-negative_edge_logic integrated \
		-control_point before \
		-minimum_bitwidth 4 \
		-max_fanout 8
}

#############################################################################
# Apply Power Optimization Constraints
#############################################################################
# Include a SAIF file, if possible, for power optimization
# read_saif -auto_map_names -input ${DESIGN_NAME}.saif -instance < DESIGN_INSTANCE > -verbose
if {[shell_is_in_topographical_mode]} {
    # Enable power prediction for this DC-T session using clock tree estimation.
    set_power_prediction true
}

# set_max_leakage_power 0
# set_max_dynamic_power 0
set_max_total_power 0

if {[shell_is_in_topographical_mode]} {
    # Specify ignored layers for routing to improve correlation
    # Use the same ignored layers that will be used during place and route
    if { $DCT_IGNORED_ROUTING_LAYERS != ""} {
        set_ignored_layers $DCT_IGNORED_ROUTING_LAYERS
    }
    report_ignored_layers

    # Apply Physical Design Constraints
    # set_fuzzy_query_options -hierarchical_separators {/ _ .} \
    # -bus_name_notations {[] __ ()} \
    # -class {cell pin port net} \
    # -show
    #extract_physical_constraints $ICPRO_DIR/units/top/export/encounter/$DESIGN_NAME.def
    extract_physical_constraints ./$DESIGN_NAME.def
    # OR
    # source -echo -verbose ${DESIGN_NAME}.physical_constraints.tcl
}

#
# check design
#
echo "Information: Checking design (see '$REPORTS_DIR/$DESIGN_NAME.check_design'). "

check_design > $REPORTS_DIR/$DESIGN_NAME.check_design


#########################################################
# Apply Additional Optimization Constraints
#########################################################

# Prevent assignment statements in the Verilog netlist.
set_fix_multiple_port_nets -all -buffer_constants
set verilogout_no_tri true

# Uniquify design
uniquify -dont_skip_empty_designs

#########################################################
# Compile the Design
#
# Recommended Options:
#
# -scan
# -retime
# -timing_high_effort_script
# -area_high_effort_script
#
#########################################################
echo "Information: Starting top down compilation (compile_ultra) ... "
remove_unconnected_ports [find cell -hierarchy *]

#
# set to true to enable
# enable scan insertion during compilation
#
if { %s } {
    # compile design using scan ffs
    compile_ultra -scan

    #
    # modify insert_scan_script template for your DFT requirements
    #
    set insert_scan_script "./scripts/${DESIGN_NAME}.insert_scan.tcl"
    if { ! [file exists $insert_scan_script] } {
      echo "ERROR: Insert scan script '$insert_scan_script' not found. "
      exit 1
    } else {
      source $insert_scan_script
    }
} else {
    # compilation without scan insertion
	# added option to keep hierarchy

    compile_ultra %s
}

echo "Information: Finished top down compilation. "

#################################################################################
# Write Out Final Design
#################################################################################
remove_unconnected_ports [find cell -hierarchy *]
change_names -rules verilog -hierarchy

echo "Information: Writing results to '$RESULTS_DIR' ... "
write -format ddc -hierarchy -output $RESULTS_DIR/${DESIGN_NAME}.ddc
write -f verilog -hier -output $RESULTS_DIR/${DESIGN_NAME}.v

if {[shell_is_in_topographical_mode]} {
	# write_milkyway uses: mw_logic1_net, mw_logic0_net and mw_design_library variables from dc_setup.tcl
	#write_milkyway -overwrite -output ${DESIGN_NAME}_DCT

	write_physical_constraints -output ${RESULTS_DIR}/${DESIGN_NAME}.mapped.physical_constraints.tcl

	# Do not write out net RC info into SDC
	set write_sdc_output_lumped_net_capacitance false
	set write_sdc_output_net_resistance false
}

# Write SDF backannotation data
write_sdf $RESULTS_DIR/${DESIGN_NAME}.sdf
write_sdc -nosplit $RESULTS_DIR/${DESIGN_NAME}.sdc

echo "Information: Writing reports to '$REPORTS_DIR' ... "
#
# check timing/contraints
#
report_design              > $REPORTS_DIR/$DESIGN_NAME.report_design
check_timing               > $REPORTS_DIR/$DESIGN_NAME.check_timing
report_port                > $REPORTS_DIR/$DESIGN_NAME.report_port
report_timing_requirements > $REPORTS_DIR/$DESIGN_NAME.report_timing_requirements
report_clock               > $REPORTS_DIR/$DESIGN_NAME.report_clock
report_constraint          > $REPORTS_DIR/$DESIGN_NAME.report_constraint

set timing_bidirectional_pin_max_transition_checks "driver"
report_constraint -max_transition  -all_vio       >> $REPORTS_DIR/$DESIGN_NAME.report_constraint

set timing_bidirectional_pin_max_transition_checks "load"
report_constraint -max_transition  -all_vio       >> $REPORTS_DIR/$DESIGN_NAME.report_constraint

report_constraints -all_violators > ${REPORTS_DIR}/${DESIGN_NAME}.report_constraints_all_violators

#
# report design
#
report_timing -max_paths 10    > $REPORTS_DIR/$DESIGN_NAME.report_timing
report_area                    > $REPORTS_DIR/$DESIGN_NAME.report_area
report_power                   > $REPORTS_DIR/$DESIGN_NAME.report_power
report_fsm                     > $REPORTS_DIR/$DESIGN_NAME.report_fsm

exit
"""
