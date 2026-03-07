<script lang="ts">
	import type { RifleSquadData, Vec2 } from '$lib/api';
	import FriendlyRifleSquad from './svg-icons/friendly-rifle-squad.svelte';
	import HostileRifleSquad from './svg-icons/hostile-rifle-squad.svelte';

	let { rifleSquadData = $bindable<RifleSquadData>() } = $props();

	const FOV_HALF = 45;
	const FOV_LENGTH = 120;
	function ray(angleDeg: number) {
		const r = (angleDeg * Math.PI) / 180;
		return {
			x: Math.cos(r) * FOV_LENGTH,
			y: Math.sin(r) * FOV_LENGTH
		};
	}

	let leftRay: Vec2 = $derived(ray(rifleSquadData.degree - FOV_HALF));
	let rightRay: Vec2 = $derived(ray(rifleSquadData.degree + FOV_HALF));
</script>

<svg overflow="visible">
	<g transform="translate({rifleSquadData.position.x},{rifleSquadData.position.y})">
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
		/>
		<line
			x1="0"
			y1="0"
			x2={rightRay.x}
			y2={rightRay.y}
			stroke="#888"
			stroke-width="1"
			stroke-dasharray="4 4"
			stroke-opacity="0.5"
		/>

		{#if rifleSquadData.isFriendly}
			<FriendlyRifleSquad />
		{:else}
			<HostileRifleSquad />
		{/if}
	</g>
</svg>
