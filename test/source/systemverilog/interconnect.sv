module interconn();
	interconnect cable;
	logic[7:0] in;
	logic[7:0] result;
	logic clk;

	dac dac_i(.in(in),.out(cable));
	adc adc_i(.clk(clk), .in(cable),.out(result));

	//always @(negedge clk) begin
	//	$display("%h",result);
	//end

	initial begin
		in = 8'h0f;
		clk = 0;
		#10ns;
		in = 8'hf0;
		#10ns;
		$finish();
	end

	always begin
		#2ns clk = ~clk;
	end
endmodule
