
# Example code from 14.1 manual
# Set all relative tolerances to 2%, constraint tolerance 
# to 3%, power tolerance to 5%. Set absolute tolerance 
# values for constraint, transition, leakage, and power

compare_library \
    -cells {DFD1} \
    -gui tt_1p2_25.cmp.gui \
    -reltol { all 0.02 constraint 0.03 power 0.05 } \
    -abstol { constraint 5e-12 trans 5.0e-12 leakage 2.e-15 power 3e-15 } \
    /cad/libs/tsmc65/digital/Front_End/timing_power_noise/NLDM/tcbn65lp_200a/tcbn65lptc.lib \
    tt_1p2_25.lib

compare_library \
    -cells {DFD1} \
    -gui brick_test_data_ffs.cmp.gui \
    -reltol { all 0.02 constraint 0.03 power 0.05 } \
    -abstol { constraint 5e-12 trans 5.0e-12 leakage 2.e-15 power 3e-15 } \
    /cad/libs/tsmc65/digital/Front_End/timing_power_noise/NLDM/tcbn65lp_200a/tcbn65lptc.lib \
    ./brick_test_data_ffs.lib
