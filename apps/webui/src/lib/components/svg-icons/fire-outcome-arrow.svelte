<script lang="ts">
	import type { Vec2 } from '$lib/api';
	import Arrow from './arrow.svelte';

	type Props = {
		from: Vec2;
		to: Vec2;
		effectLabel: string;
	};

	let props: Props = $props();
</script>

<svg>
	<Arrow
		start={props.from}
		end={props.to}
		headOffset={7}
		shaftWidth={2.5}
		headSize={5}
		text={props.effectLabel}
	/>
</svg>
