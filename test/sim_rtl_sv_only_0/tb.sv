`timescale 1ns/10ps

module tb();
	logic clk;
	logic a;

	initial begin
		clk = 0;
		a = 0;
	end
	always begin
		#5 clk = ~clk;
	end

	top top_i(clk,a,a);
endmodule
