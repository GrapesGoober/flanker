<script lang="ts">
	import type { RifleSquadData } from '$lib/api';
	import FriendlyRifleSquad from './svg-icons/friendly-rifle-squad.svelte';
	import HostileRifleSquad from './svg-icons/hostile-rifle-squad.svelte';

	let { rifleSquadData = $bindable<RifleSquadData>() } = $props();
</script>

<svg overflow="visible">
	<g transform="translate({rifleSquadData.position.x},{rifleSquadData.position.y})">
		{#if rifleSquadData.isFriendly}
			<FriendlyRifleSquad />
		{:else}
			<HostileRifleSquad />
		{/if}
	</g>
</svg>
