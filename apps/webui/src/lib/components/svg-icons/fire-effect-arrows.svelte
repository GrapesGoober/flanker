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
		<g transform="translate(0, 0)">
			<Arrow
				start={props.positionA}
				end={props.positionB}
				headOffset={7}
				shaftWidth={2.5}
				headSize={5}
			/>
			<g
				transform="
                translate({props.positionA.x}, {props.positionA.y}) 
                rotate({angle})
            	"
			>
				<g transform="translate({length / 3}, 0)">
					<foreignObject
						x={0}
						y={-8}
						width="160"
						height="160"
						class="fire-effect-text"
					>
						{props.fireEffectA}
					</foreignObject>
				</g>
			</g>
		</g>
	{/if}

	{#if props.fireEffectB != null}
		<g transform="translate(0, 0)">
			<Arrow
				start={props.positionB}
				end={props.positionA}
				headOffset={7}
				shaftWidth={2.5}
				headSize={5}
			/>
			<g
				transform="
                translate({props.positionB.x}, {props.positionB.y}) 
                rotate({angle - 180})
            	"
			>
				<g transform="translate({length / 3}, 0)">
					<foreignObject
						x={0}
						y={-8}
						width="160"
						height="160"
						class="fire-effect-text"
					>
						{props.fireEffectB} FIRE
					</foreignObject>
				</g>
			</g>
		</g>
	{/if}
</svg>

<style lang="less">
	.fire-effect-text {
		font-size: 0.3em;
	}
</style>
