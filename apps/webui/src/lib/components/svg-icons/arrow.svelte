<script lang="ts">
	import type { Vec2 } from '$lib/api';

	type Props = {
		start: Vec2;
		end: Vec2;
		headOffset: number;
		headSize: number;
		shaftWidth: number;
	};

	let props: Props = $props();

	const angle = $derived(
		(Math.atan2(props.end.y - props.start.y, props.end.x - props.start.x) *
			180) /
			Math.PI
	);

	const length = $derived(
		Math.hypot(props.end.x - props.start.x, props.end.y - props.start.y) -
			props.headOffset
	);
</script>

<svg>
	<g
		transform={`translate(${props.start.x} ${props.start.y}) rotate(${angle})`}
	>
		<polygon
			points={`
				0,${-props.shaftWidth / 2}
				${length - props.headSize},${-props.shaftWidth / 2}
				${length - props.headSize},${-props.headSize / 2}
				${length},0
				${length - props.headSize},${props.headSize / 2}
				${length - props.headSize},${props.shaftWidth / 2}
				0,${props.shaftWidth / 2}
			`}
		/>

		<g transform={`translate(${length / 4} 0)`}>
			<foreignObject x={0} y={-8} width="160" height="160" class="arrow-text">
				hello world
			</foreignObject>
		</g>
	</g>
</svg>

<style lang="less">
	.arrow-text {
		font-size: 0.3em;
	}
</style>
