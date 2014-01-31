
module tb();
	logic clk;
	logic a;

	initial begin
		clk = 0;
		$deposit(a,0);
		#50;
		$finish();
	end
	always begin
		#5 clk = ~clk;
	end

	top top_i(clk,a,a);
endmodule
 
 
 
