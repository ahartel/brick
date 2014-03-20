
module top(
	input reg clk,a,
	output reg b
);
	always @(posedge clk) begin
		b <= ~a;
	end
endmodule
 
 
