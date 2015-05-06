
module top(
	input logic clk,
	input logic[1:0] a,
	output logic[1:0] b
);
	wire[1:0] not_a;
	inverter_array inv_array(a,not_a);
	always @(posedge clk) begin
		b <= not_a;
	end
endmodule
