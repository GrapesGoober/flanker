<script lang="ts">
	import type { Vec2 } from '$lib/api';
	import Arrow from './arrow.svelte';

	type Props = {
		start: Vec2;
		end: Vec2;
		headOffset: number;
	};

	let props: Props = $props();
</script>

<svg>
	<Arrow
		start={props.start}
		end={props.end}
		headOffset={props.headOffset}
		headSize={10}
		shaftWidth={4}
	/>
</svg>
