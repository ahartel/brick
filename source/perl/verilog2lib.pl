#!/usr/bin/perl
#
# created by Andreas Gruebl, updated to include parasitics 16.11.2010
#

use Getopt::Long;

print "Verilog to basic Liberty format converter\n";

$pexfile;

my %Options;
GetOptions(\%Options,'ignore-pin=s@');

# parse input arguments
if($#ARGV < 1){
	print "Usage: verilog2lib.pl [--ignore-pin <pin name>]... <infile.v> <outfile.lib> [pincapfile(optional)]\n";
	die;
} elsif ($#ARGV == 2) {
	$in=$ARGV[0];
	$out=$ARGV[1];
	$pexfile=$ARGV[2];
} else {
#	print "\n***** not using any extra pin capacitance information! *****\n\n";
	$in=$ARGV[0];
	$out=$ARGV[1];
}

# check files
open(BASE,$in) or die "Can't open $in";
open(NEW,'>',$out) or die "Can't open $out";

open(PEXF,$pexfile) or print "\n***** not using any extra pin capacitance information! *****\n\n";
close(PEXF);

$date = qx(date); $date =~ s/\n//;

#determine cell name:
$cell_name = "trullala";
while($line=<BASE>){
	($mod,$name,$etc)=split(" ",$line);
	if($mod eq "module"){
		$cell_name = $name;
		last;
	}
}

# start with default library header
print NEW "library(${cell_name}_wc) {

	date : \"$date\";
	comment : \"Generated automatically by verilog2lib.pl\";
	technology (cmos) ;
";

# insert delay model definition
if($pexfile ne "") {
	open(PEXF,'<',$pexfile) or die "Can't open $pexfile";
	$insert = 0;
	while($pexline=<PEXF>){
		@content=split(" ",$pexline);
		$content[0] =~ s/\n//;
		$content[1] =~ s/\n//;
		if($content[0] eq "+td"){
			print NEW "\tdelay_model : $content[1]\n\n";
		}
	}
} else {
	print NEW "\tdelay_model : generic_cmos ;\n\n";
}

# continue with standard header
print NEW "	time_unit : \"1ns\" ;
	voltage_unit : \"1V\" ;
	current_unit : \"1uA\" ;
	leakage_power_unit : \"1uW\" ;
	capacitive_load_unit(1,pf) ;
	pulling_resistance_unit : \"1kohm\" ;
	nom_process		: 1.0;
	nom_voltage		: 1.62;
	nom_temperature	: 125;

	default_fanout_load : 1 ;
	default_inout_pin_cap : 1 ;
	default_input_pin_cap : 1 ;
	default_output_pin_cap : 0 ;
	default_cell_leakage_power : 0 ;
	default_leakage_power_density : 0 ;

	default_max_transition : 5 ;
	in_place_swap_mode : no_swapping ;

	slew_lower_threshold_pct_rise : 10.0 ;
	slew_upper_threshold_pct_rise : 90.0 ;
	slew_lower_threshold_pct_fall : 10.0 ;
	slew_upper_threshold_pct_fall : 90.0 ;
	slew_derate_from_library      :  1.0 ; 
	input_threshold_pct_fall      : 50.0 ;
	output_threshold_pct_fall     : 50.0 ;
	input_threshold_pct_rise      : 50.0 ;
	output_threshold_pct_rise     : 50.0 ;

";

# insert potential lookup table definitions for table_lookup model
if($pexfile ne "") {
	open(PEXF,'<',$pexfile) or die "Can't open $pexfile";
	$insert = 0;
	while($lutline=<PEXF>){
		@content=split(" ",$lutline);
		$content[0] =~ s/\n//;
		$content[1] =~ s/\n//;
		if($insert == 0) {
			if($content[0] eq "+ld"){
				$insert = 1;
			}
		} else {
			if($content[0] eq "-ld"){
				$insert = 0;
				last;
			} else {
				print NEW "\t$lutline";
			}
		}
	}
	print NEW "\n";
	close(PEXF);
}
  

my %types = ();

# now, first generate bus types:
while($line=<BASE>){
	($dir,$i1,$i2)=split(" ",$line);
	if($dir eq "input" or $dir eq "output" or $dir eq "inout"){ # is a port processed?
		if($i1 =~ "\:"){ # if yes, a bus is processed, if not a pin
			($fi,$li) = split(":",$i1); # get index values
			$fi =~ s/\[//;
			$li =~ s/\]//;
			if($fi > $li){ # generate bus type
				$size = $fi + 1;
				$type = "bus_$size";
				$dt = "true";
			} else {
				$size = $li + 1;
				$type = "bus_${size}f";
				$dt = "false";
			}
			if(not exists $types{$type}) {
				print NEW "\ttype ($type) {\n\t\tbase_type : array;\n\t\tbit_width : $size;\n\t\tbit_from : $fi;\n\t\tbit_to : $li;\n\t\tdata_type : bit;\n\t\tdownto : $dt;\n\t}\n\n";
				$types{$type} = 1
			}
		}
	}
}


print NEW "\n\tcell (${cell_name}) {\n\n";

close(BASE);
open(BASE,$in) or die "Can't open $in";

%namemap = ();

# then generate pin / bus entries
while($line=<BASE>){
	my $ignored = 0;
	($dir,$i1,$i2)=split(" ",$line);
	if($dir eq "input" or $dir eq "output" or $dir eq "inout"){ # is a port processed?
		if($i1 =~ "\:"){ # if yes, a bus is processed, if not a pin
			$name = $i2;
			$name =~ s/[;\\]//;
			($fi,$li) = split(":",$i1); # get index values
			$fi =~ s/\[//;
			$li =~ s/\]//;
			if($fi > $li){ # generate bus type
				$size = $fi + 1;
				$type = "bus_$size";
			} else {
				$size = $li + 1;
				$type = "bus_${size}f";
			}
			print NEW "\t\tbus ( $name ) {\n\t\t\tbus_type  : $type;\n\t\t\tdirection : $dir;\n";
		} else {
			$name = $i1;
			$name =~ s/[;\\]//;
			# search for pin name in ignored pin list
			foreach my $ignored_pin (@{$Options{'ignore-pin'}}) {
				if ($ignored_pin eq $name) {
					$ignored = 1;
					last;
				}
			}
			if (!$ignored) {
				$type = "pin";
				print NEW "\t\tpin ( \"$name\" ) {\n\t\t\tdirection : $dir;\n";
			}
		}
		# insert pin parasitics if available
		if($pexfile ne "" && !$ignored) {
			open(PEXF,'<',$pexfile) or die "Can't open $pexfile";
			$insert = 0;
			while($pexline=<PEXF>){
				@content=split(" ",$pexline);
				$content[0] =~ s/\n//;
				$content[1] =~ s/\n//;
				if($insert == 0){
					if(($content[0] eq "+pd") && ($content[1] ne "") && ($namemap{$content[1]} != 1)){
						$namemap{$content[1]} = 0;
					}
					if($content[1] eq $name){
						print "Adding extra information for pin/bus $content[1]\n";
						$insert = 1;
						$namemap{$content[1]} = 1;
					}
				} else {
					if($content[0] eq "-pd"){
						$insert = 0;
						last;
					} else {
						print NEW "\t\t\t$pexline";
					}
				}
			}
			close(PEXF);
		}
		print NEW "\t\t}\n\n" if (!$ignored);
	}
}
print NEW "\t}\n}\n";
close(BASE);
close(NEW);

for my $n ( keys %namemap ){
	my $ignored = 0;
	# search for pin name in ignored pin list
	foreach my $ignored_pin (@{$Options{'ignore-pin'}}) {
		if ($ignored_pin eq $n) {
			$ignored = 1;
			last;
		}
	}
	if($namemap{$n} == 0 && !$ignored) {
		print "\n**************************************************************************\n";
		print "*** ERROR: Pin $n in parasitics definition not found in timing library!\n";
		print "**************************************************************************\n\n";
	}
}


