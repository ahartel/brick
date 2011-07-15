; generate functional view from schematic
; Andreas Gruebl, 16.11.2010

library = getShellEnvVar("LIB")
block = getShellEnvVar("BLOCK")
sourceview = "schematic"
targetview = "functional"

ddDeleteLocal( ddGetObj( library block targetview ""))
schViewToView( library block library block sourceview targetview "schSchemToPinList" "schPinListToVerilog" )

exit()

 
