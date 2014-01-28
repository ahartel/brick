

module top(clk,a,b);
	always (@posedge clk)
		b <= ~a;
	end
endmodule
