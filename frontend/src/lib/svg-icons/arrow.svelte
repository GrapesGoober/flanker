<script lang="ts">
	import type { Vec2 } from '$lib';

	type Props = {
		start: Vec2;
		end: Vec2;
	};
	let props: Props = $props();

	function GetShaftEnd(): Vec2 {
		// Normalized directional vector of this arrow
		const dx = props.end.x - props.start.x;
		const dy = props.end.y - props.start.y;
		const length = Math.hypot(dx, dy);
		const ux = dx / length;
		const uy = dy / length;

		// Point before arrowhead starts
		const HEADLENGTH = 6;
		return {
			x: props.end.x - ux * HEADLENGTH,
			y: props.end.y - uy * HEADLENGTH
		};
	}

	let shaftEnd: Vec2 = $derived(GetShaftEnd());
</script>

<defs>
	<marker
		id="triangle"
		viewBox="0 0 8 8"
		refX="1"
		refY="4"
		markerUnits="strokeWidth"
		markerWidth="2"
		markerHeight="2"
		orient="auto"
	>
		<path d="M 0 0 L 6 4 L 0 8 z" />
	</marker>
</defs>

<line
	x1={props.start.x}
	y1={props.start.y}
	x2={shaftEnd.x}
	y2={shaftEnd.y}
	class="move-line"
	marker-end="url(#triangle)"
/>

<style lang="less">
	@color: black;
	path {
		stroke: none;
		fill: @color;
	}
	line {
		stroke-width: 5;
		stroke: @color;
	}
</style>
