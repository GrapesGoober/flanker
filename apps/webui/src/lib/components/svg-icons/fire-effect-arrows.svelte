<script lang="ts">
	import type { FireEffect, Vec2 } from '$lib/api';
	import Arrow from './arrow.svelte';

	const arrowHeadOffset = 15;
	type Props = {
		positionA: Vec2;
		positionB: Vec2;
		fireEffectA: FireEffect | null;
		fireEffectB: FireEffect | null;
	};
	let props: Props = $props();
</script>

{#if props.fireEffectA != null}
	<Arrow
		start={props.positionA}
		end={props.positionB}
		headOffset={arrowHeadOffset}
		shaftWidth={2.5}
		headSize={5}
	/>
{/if}
