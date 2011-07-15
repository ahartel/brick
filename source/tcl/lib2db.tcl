# converts all *.lib files within ./timing to their corresponding synopsys *.db files
#
# created 17.11.2010 by Andreas Gruebl
#

set files [split [glob timing/*.lib] " "]

foreach file $files {
	read_lib $file
	set libname [lindex [split [lindex [split $file "/"] [expr [llength [split $file "/"]]-1]] "."] 0]
	write_lib -output timing/${libname}.db $libname
}

exit

