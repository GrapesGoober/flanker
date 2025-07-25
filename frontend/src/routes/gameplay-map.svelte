<script lang="ts">
	import { onMount } from 'svelte';
	import RifleSquad from '$lib/rifle-squad.svelte';
	import SvgMap from '$lib/map/svg-map.svelte';
	import Arrow from '$lib/svg-icons/arrow.svelte';
	import { PlayerController } from './player-controller.svelte';
	import BlankUnit from '$lib/svg-icons/blank-unit.svelte';

	let { controller = $bindable<PlayerController>() } = $props();
	let map: SvgMap | null = $state(null);
	let clickTarget: HTMLElement | null = $state(null);

	onMount(async () => {
		await controller.initializeAsync();
	});

	function AddMarker(event: MouseEvent) {
		if (map == null) return;
		const node = clickTarget as HTMLElement;
		const rect = node.getBoundingClientRect();
		const x = event.clientX - rect.x;
		const y = event.clientY - rect.y;
		controller.setMoveMarker(map.ToWorldCoords({ x, y }));
	}

	function SelectUnit(unitId: number, event: MouseEvent) {
		event.stopPropagation(); // Prevent the terrain's onclick trigger
		controller.selectUnit(unitId);
	}
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
{#snippet mapSvgSnippet()}
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
			{:else if controller.state.type == 'fireMarked'}
				{@const target = controller.state.target.position}
				<Arrow start={selectedUnit.position} end={target} offset={15} />
			{/if}
		{/if}
	</g>

	{#each controller.unitData.squads as unit, index}
		<g onclick={(event) => SelectUnit(unit.unitId, event)}>
			<RifleSquad bind:rifleSquadData={controller.unitData.squads[index]} />
		</g>
	{/each}
{/snippet}

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div bind:this={clickTarget} onclick={AddMarker}>
	<SvgMap svgSnippet={mapSvgSnippet} terrainData={controller.terrainData} bind:this={map} />
</div>

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
