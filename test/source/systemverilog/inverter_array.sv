
module inverter_array(
	input logic[1:0] a,
	output logic[1:0] b
);

	inverter inv[1:0](a,b);

endmodule
