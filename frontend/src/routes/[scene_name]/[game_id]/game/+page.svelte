<script lang="ts">
	import { onMount } from 'svelte';
	import { PlayerController } from './player-controller.svelte';
	import ControlPanel from './control-panel.svelte';
	import { SvgMap } from '$lib/components';
	import TerrainLayer from './terrain-layer.svelte';
	import CombatUnitsLayer from './combat-units-layer.svelte';

	let controller: PlayerController = $state(new PlayerController());
	let map: SvgMap | null = $state(null);
	let clickTarget: HTMLElement | null = $state(null);

	function AddMarker(event: MouseEvent) {
		if (map == null) return;
		if (controller.isFetching) return;
		const node = clickTarget as HTMLElement;
		const rect = node.getBoundingClientRect();
		const x = event.clientX - rect.x;
		const y = event.clientY - rect.y;
		controller.setMoveMarker(map.ToWorldCoords({ x, y }));
	}
	onMount(async () => {
		await controller.initializeAsync();
	});
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
{#snippet mapSvgSnippet()}
	<TerrainLayer terrainData={controller.terrainData} />
	<CombatUnitsLayer bind:controller />
{/snippet}

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div bind:this={clickTarget} onclick={AddMarker}>
	<SvgMap svgSnippet={mapSvgSnippet} bind:this={map} />
</div>

<ControlPanel bind:controller />

{controller.unitData.objectiveState == 'COMPLETED' ? 'Objectives Completed' : ''}
