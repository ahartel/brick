# converts all *.lib files within ./timing to their corresponding synopsys *.db files
#
# created 17.11.2010 by Andreas Gruebl
#

set libname [getenv "LIB"]
set block [getenv "BLOCK"]
set RESULTS_DIR [getenv "RESULTS_DIR"]

set file $RESULTS_DIR/abstract/$libname/$block.lib
set output $RESULTS_DIR/abstract/$libname/$block.db

read_lib $file
append block "_wc"
write_lib -output $output $block

exit

