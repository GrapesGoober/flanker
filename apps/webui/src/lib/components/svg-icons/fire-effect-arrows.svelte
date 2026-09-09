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
		(Math.atan2(
			props.positionB.y - props.positionA.y,
			props.positionB.x - props.positionA.x
		) *
			180) /
			Math.PI
	);

	const length = $derived(
		Math.hypot(
			props.positionB.x - props.positionA.x,
			props.positionB.y - props.positionA.y
		)
	);
</script>

<svg>
	{#if props.fireEffectA != null}
		<Arrow
			start={props.positionA}
			end={props.positionB}
			headOffset={10}
			shaftWidth={2.5}
			headSize={5}
		/>
		<g
			transform="
                translate({props.positionA.x}, {props.positionA.y}) 
                rotate({angle})"
		>
			<g transform="translate({length / 3}, 0)">
				<foreignObject
					x={0}
					y={-8}
					width="160"
					height="160"
					class="fire-effect-text"
				>
					{props.fireEffectA} FIRE
				</foreignObject>
			</g>
		</g>
	{/if}
</svg>

<style lang="less">
	.fire-effect-text {
		font-size: 0.3em;
	}
</style>
