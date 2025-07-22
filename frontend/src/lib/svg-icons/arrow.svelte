<script lang="ts">
	import type { Vec2 } from '$lib';

	type Props = {
		start: Vec2;
		end: Vec2;
	};
	let props: Props = $props();
	const offset = 10;
	const dx = props.end.x - props.start.x;
	const dy = props.end.y - props.start.y;
	const len = Math.hypot(dx, dy);
	const factor = (len - offset) / len;
	let shortenLine: Vec2 = {
		x: props.start.x + dx * factor,
		y: props.start.y + dy * factor
	};
</script>

<defs>
	<marker
		id="arrow"
		viewBox="0 0 6 6"
		refX="0"
		refY="3"
		markerWidth="3"
		markerHeight="3"
		orient="auto-start-reverse"
	>
		<path d="M 0 0 L 6 3 L 0 6 z" />
	</marker>
</defs>

<line
	x1={props.start.x}
	y1={props.start.y}
	x2={shortenLine.x}
	y2={shortenLine.y}
	marker-end="url(#arrow)"
/>

<style lang="less">
	@color: rgba(0, 0, 0);
	line {
		stroke: @color;
		stroke-width: 3;
	}
	path {
		fill: @color;
	}
</style>
