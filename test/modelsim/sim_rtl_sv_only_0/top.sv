
module top(
	input logic clk,a,
	output logic b
);
	always @(posedge clk) begin
		b <= ~a;
	end
endmodule
 
 
