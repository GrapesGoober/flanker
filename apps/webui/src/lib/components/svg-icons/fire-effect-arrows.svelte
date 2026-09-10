<script lang="ts">
	import type { FireEffect, Vec2 } from '$lib/api';
	import Arrow from './arrow.svelte';

	type Props = {
		positionA: Vec2;
		positionB: Vec2;
		fireEffectA: FireEffect | null;
		fireEffectB: FireEffect | null;
	};

	let props: Props = $props();

	const angle = $derived(
		Math.atan2(
			props.positionB.y - props.positionA.y,
			props.positionB.x - props.positionA.x
		)
	);

	const distance = 3;

	const offset = $derived({
		x: -Math.sin(angle) * distance,
		y: Math.cos(angle) * distance
	});
</script>

<svg>
	{#if props.fireEffectA != null}
		<g transform={`translate(${-offset.x}, ${-offset.y})`}>
			<Arrow
				start={props.positionA}
				end={props.positionB}
				headOffset={7}
				shaftWidth={2.5}
				headSize={5}
			/>
		</g>
	{/if}

	{#if props.fireEffectB != null}
		<g transform={`translate(${offset.x}, ${offset.y})`}>
			<Arrow
				start={props.positionB}
				end={props.positionA}
				headOffset={7}
				shaftWidth={2.5}
				headSize={5}
			/>
		</g>
	{/if}
</svg>
