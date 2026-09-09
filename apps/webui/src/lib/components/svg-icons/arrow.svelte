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
	<!-- Draw arrow flat (facing rightward) then rotate it via transform -->
	<polygon
		transform={`translate(${props.start.x} ${props.start.y}) rotate(${angle})`}
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
</svg>
