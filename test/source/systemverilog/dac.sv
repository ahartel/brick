module dac(
	input logic[7:0] in,
	output real out
);
	parameter supply = 1.2;
	assign out = supply/255*in;

endmodule
