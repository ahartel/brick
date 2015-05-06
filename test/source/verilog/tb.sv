`include "wait_time.v"

module tb();
	logic clk;
	logic[1:0] a;

	initial begin
		clk = 0;
		$deposit(a,2'b00);
		#(`WAIT_TIME);
		$finish();
	end
	always begin
		#clk_period::period clk = ~clk;
	end

	top top_i(clk,a,a);

endmodule
