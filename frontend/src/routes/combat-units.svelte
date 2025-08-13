<script lang="ts">
	import RifleSquad from '$lib/rifle-squad.svelte';
	import Arrow from '$lib/svg-icons/arrow.svelte';
	import { PlayerController } from './player-controller.svelte';
	import BlankUnit from '$lib/svg-icons/blank-unit.svelte';

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
		<circle
			cx={selectedUnit.position.x}
			cy={selectedUnit.position.y}
			r="10"
			class="select-circle"
		/>
		{#if controller.state.type == 'moveMarked'}
			{@const moveMarker = controller.state.moveMarker}
			<g transform="translate({moveMarker.x}, {moveMarker.y})"><BlankUnit /></g>
			<Arrow start={selectedUnit.position} end={controller.state.moveMarker} offset={15} />
		{:else if controller.state.type == 'attackMarked'}
			{@const target = controller.state.target.position}
			<Arrow start={selectedUnit.position} end={target} offset={15} />
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
	.select-circle {
		fill: black;
	}
	.transparent-icons {
		opacity: 0.5;
	}
</style>
