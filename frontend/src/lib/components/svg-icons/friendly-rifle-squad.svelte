<svg overflow="visible">
	<rect x="-7" y="-5" width="14" height="10" class="box" />
	<line x1="-7" y1="-5" x2="7" y2="5" class="cross" />
	<line x1="7" y1="-5" x2="-7" y2="5" class="cross" />
</svg>

<style lang="less">
	@stroke-width: 0.7;
	.box {
		fill: white;
		stroke: black;
		stroke-width: @stroke-width;
	}
	.cross {
		stroke: black;
		stroke-width: @stroke-width;
	}
</style>
