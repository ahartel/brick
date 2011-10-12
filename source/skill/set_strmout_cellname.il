; modify and thereby uniquify streamed out cell names 
; in order to avoid name collisions in top level stream file
;
; created 15.12.2010, Andreas Gruebl, KIP, UHEI


block = getShellEnvVar("BLOCK")

procedure( poCellNameMap( lib cell view )
	prog( ( mapname )
		if( cell == block then
			return( cell )
		else
			sprintf( mapName "%s_%s_%s" cell lib block)
			return( mapName )
		)
	);prog
);procedure

procedure( poParamCellNameMap( name ID )
	prog( ( newName )
		sprintf( newName "%s_%s_%s" name block ID )
		return( newName )
	);prog
);procedure
