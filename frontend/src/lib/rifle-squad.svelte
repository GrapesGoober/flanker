<script lang="ts">
	import type { RifleSquadData } from '$lib';
	import FriendlyRifleSquad from './svg-icons/friendly-rifle-squad.svelte';
	import HostileRifleSquad from './svg-icons/hostile-rifle-squad.svelte';
	let { rifleSquadData = $bindable() }: { rifleSquadData: RifleSquadData } = $props();
</script>

<g transform="translate({rifleSquadData.position.x},{rifleSquadData.position.y})">
	{#if rifleSquadData.isFriendly}
		<g class={rifleSquadData.isSelected ? 'unit-icon-selected' : 'unit-icon'}>
			<FriendlyRifleSquad />
		</g>
	{:else}
		<HostileRifleSquad />
	{/if}
</g>

<style>
	.unit-icon {
		transform: scale(1, 1);
	}
	.unit-icon-selected {
		transform: scale(1.1, 1.1);
	}
</style>
