<script lang="ts">
	import RifleSquad from '$lib/rifle-squad.svelte';
	import Arrow from '$lib/svg-icons/arrow.svelte';
	import { PlayerController } from './player-controller.svelte';
	import BlankUnit from '$lib/svg-icons/blank-friendly-unit.svelte';
	import BorderFriendlyUnit from '$lib/svg-icons/border-friendly-unit.svelte';
	import BorderHostileUnit from '$lib/svg-icons/border-hostile-unit.svelte';

	type Props = {
		controller: PlayerController;
	};

	let { controller = $bindable() }: Props = $props();

	function SelectUnit(unitId: number, event: MouseEvent) {
		if (controller.isFetching) return;
		event.stopPropagation(); // Prevent the terrain's onclick trigger
		controller.selectUnit(unitId);
	}
</script>

<!-- Defines overlay for gameplay icons -->
<g class="transparent-icons">
	{#if controller.state.type !== 'default'}
		{@const selectedUnit = controller.state.selectedUnit}
		{@const position = controller.state.selectedUnit.position}

		{#if selectedUnit.isFriendly}
			<g transform="translate({position.x}, {position.y})"><BorderFriendlyUnit /></g>
		{:else if !selectedUnit.isFriendly}
			<g transform="translate({position.x}, {position.y})"><BorderHostileUnit /></g>
		{/if}
		{#if controller.state.type == 'moveMarked'}
			{@const moveMarker = controller.state.moveMarker}
			<g transform="translate({moveMarker.x}, {moveMarker.y})"><BlankUnit /></g>
			<Arrow start={selectedUnit.position} end={controller.state.moveMarker} offset={6} />
		{:else if controller.state.type == 'attackMarked'}
			{@const targetPos = controller.state.target.position}
			<Arrow start={selectedUnit.position} end={targetPos} offset={12} />
			<g transform="translate({targetPos.x}, {targetPos.y})"><BorderHostileUnit /></g>
		{/if}
	{/if}
</g>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<!-- Draw combat units -->
{#each controller.unitData.squads as unit, index}
	<g onclick={(event) => SelectUnit(unit.unitId, event)}>
		<RifleSquad bind:rifleSquadData={controller.unitData.squads[index]} />
	</g>
{/each}

<style lang="less">
	* {
		font-size: large;
		font-family: Verdana, Geneva, Tahoma, sans-serif;
	}
	.transparent-icons {
		opacity: 0.5;
	}
</style>
