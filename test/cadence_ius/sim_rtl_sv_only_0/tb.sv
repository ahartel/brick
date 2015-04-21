`include "wait_time.v"

module tb();
	logic clk;
	logic a;

	initial begin
		clk = 0;
		$deposit(a,0);
		#(`WAIT_TIME);
		$finish();
	end
	always begin
		#clk_period::period clk = ~clk;
	end

	top top_i(clk,a,a);

endmodule
