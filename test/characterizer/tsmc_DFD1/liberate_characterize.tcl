# Define templates for characterization.
# Delay template for 3 input slews and 3 loads
define_template -type delay \
    -index_1 {0.0049 0.0125 0.0277 0.0582 0.1192 0.2412 0.4851} \
    -index_2 {0.00077 0.0017 0.00355 0.00725 0.01466 0.02947 0.0591} \
    delay_7x7

# Power template for 3 input slews and 3 loads
define_template -type power \
    -index_1 {0.0049 0.0125 0.0277 0.0582 0.1192 0.2412 0.4851} \
    -index_2 {0.00077 0.0017 0.00355 0.00725 0.01466 0.02947 0.0591} \
    power_7x7

# Timing constraint template for 3 input slews 
define_template -type constraint \
    -index_1 {0.0049 0.0582 0.4851} \
    -index_2 {0.0049 0.0582 0.4851} \
    constraint_3x3

# Specify the PVT for this characterization run
set_operating_condition -voltage 1.2 -temp 25

# Set the output transition thresholds to 30-70%
set_var slew_normalize 1
set_var slew_lower_fall 0.1
set_var slew_upper_fall 0.9
set_var slew_lower_rise 0.1
set_var slew_upper_rise 0.9

# Read in the SPICE subckts and models
#read_spice {./results/DFD1_wrapper.pex.netlist}
#read_spice -format spectre {../../../../source/spice/include_all_models_tsmc.scs}
read_spice -format spectre {../inclusion_wrapper.scs}

# Define how to characterize each group of cells
define_cell \
    -input {D} \
    -output {Q QN} \
    -clock {CP} \
    -async {} \
    -delay delay_7x7 \
    -power power_7x7 \
    -constraint constraint_3x3 \
    {DFD1}

# Perform characterization and write out the library
char_library

write_library -overwrite tt_1p2_25.lib

