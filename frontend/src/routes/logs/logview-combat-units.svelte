<script lang="ts">
	import type { CombatUnitsViewState } from '$lib';
	import RifleSquad from '$lib/rifle-squad.svelte';

	type Props = {
		unitData: CombatUnitsViewState;
	};

	let { unitData = $bindable() }: Props = $props();
</script>

{#each unitData.squads as unit, index}
	<RifleSquad bind:rifleSquadData={unitData.squads[index]} />
{/each}
