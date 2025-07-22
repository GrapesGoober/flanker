<script lang="ts">
	import type { Vec2 } from '$lib';
	import * as d3 from 'd3';

	type Props = {
		start: Vec2;
		end: Vec2;
	};
	let props: Props = $props();

	const headLength = 8;
	const headWidth = 2;
	const headOffset = 5;
	function GetPoints() {
		// Normalized directional vector of this arrow
		const dx = props.end.x - props.start.x;
		const dy = props.end.y - props.start.y;
		const length = Math.hypot(dx, dy);
		const ux = dx / length;
		const uy = dy / length;

		// Point before arrowhead starts
		const shaftEnd: Vec2 = {
			x: props.end.x - ux * headLength,
			y: props.end.y - uy * headLength
		};

		// Perpendicular vector for head width
		const perpX = -uy;
		const perpY = ux;

		// Arrowhead points (triangle)
		const leftHead: Vec2 = {
			x: shaftEnd.x + perpX * headWidth,
			y: shaftEnd.y + perpY * headWidth
		};
		const rightHead: Vec2 = {
			x: shaftEnd.x - perpX * headWidth,
			y: shaftEnd.y - perpY * headWidth
		};
		const top: Vec2 = {
			x: props.end.x - ux * headOffset,
			y: props.end.y - uy * headOffset
		};

		return [props.start, shaftEnd, leftHead, top, rightHead, shaftEnd];
	}

	function GetPath(coords: Vec2[]): string {
		const line = d3
			.line<Vec2>()
			.x((d) => d.x)
			.y((d) => d.y)
			.curve(d3.curveCardinal.tension(1));
		return line(coords) || '';
	}

	let path: string = $derived(GetPath(GetPoints()));
</script>

<path d={path} />

<style lang="less">
	@color: rgba(0, 0, 0, 0.5);
	path {
		fill: none;
		stroke: @color;
		stroke-width: 5;
	}
</style>
