<script lang="ts">
	import type { RifleSquadData, Vec2 } from '$lib/api';
	import FriendlyRifleSquad from './svg-icons/friendly-rifle-squad.svelte';
	import HostileRifleSquad from './svg-icons/hostile-rifle-squad.svelte';

	type Props = {
		rifleSquadData: RifleSquadData;
	};

	let { rifleSquadData = $bindable() }: Props = $props();

	const FOV_LENGTH = 120;

	function ray(angleDeg: number) {
		const r = (angleDeg * Math.PI) / 180;
		return {
			x: Math.cos(r) * FOV_LENGTH,
			y: Math.sin(r) * FOV_LENGTH
		};
	}

	let leftRay: Vec2 | null = $derived.by(() => {
		if (rifleSquadData.fovDegrees == null) return null;
		const FOV_HALF = rifleSquadData.fovDegrees / 2;
		return ray(rifleSquadData.degree - FOV_HALF);
	});
	let rightRay: Vec2 | null = $derived.by(() => {
		if (rifleSquadData.fovDegrees == null) return null;
		const FOV_HALF = rifleSquadData.fovDegrees / 2;
		return ray(rifleSquadData.degree + FOV_HALF);
	});
</script>

<svg overflow="visible">
	<g
		transform="translate({rifleSquadData.position.x},{rifleSquadData.position
			.y})"
	>
		{#if leftRay != null}
			<!-- FOV lines -->
			<line
				x1="0"
				y1="0"
				x2={leftRay.x}
				y2={leftRay.y}
				stroke="#888"
				stroke-width="1"
				stroke-dasharray="4 4"
				stroke-opacity="0.5"
				pointer-events="none"
			/>
		{/if}
		{#if rightRay != null}
			<line
				x1="0"
				y1="0"
				x2={rightRay.x}
				y2={rightRay.y}
				stroke="#888"
				stroke-width="1"
				stroke-dasharray="4 4"
				stroke-opacity="0.5"
				pointer-events="none"
			/>
		{/if}

		{#if rifleSquadData.isFriendly}
			<FriendlyRifleSquad />
		{:else}
			<HostileRifleSquad />
		{/if}
	</g>
</svg>
