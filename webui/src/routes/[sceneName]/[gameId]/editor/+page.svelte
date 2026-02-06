<script lang="ts">
	/**
	 * Editor page for terrain and polygon drawing in the map scene.
	 * Handles terrain editing, drawing polygons, and UI state management.
	 */
	import { SvgMap } from '$lib/components';
	import TerrainLayer from '$lib/components/terrain-layer.svelte';
	import { GetSmoothedClosedPath } from '$lib/map-utils';
	import { onMount } from 'svelte';
	import { EditorController } from './editor-controller.svelte';
	import EditorTerrainLayer from './editor-terrain-layer.svelte';

	let controller: EditorController = $state(new EditorController());
	let map: SvgMap | null = $state(null);
	let clickTarget: HTMLElement | null = $state(null);
	let currentChosenWaypointsFaction: 'BLUE' | 'RED' = $state('RED');

	/// Refreshes terrain data when the component mounts. */
	onMount(() => {
		controller.refreshTerrain();
	});

	/** Handles click as adding a vertex or waypoint, depending on state. */
	function handleClick(event: MouseEvent) {
		if (map == null) return;
		const node = clickTarget as HTMLElement;
		const rect = node.getBoundingClientRect();
		const x = event.clientX - rect.x;
		const y = event.clientY - rect.y;
		let worldPos = map.ToWorldCoords({ x, y });
		controller.addVertex(worldPos);
		controller.addWaypoint(worldPos);
	}

	/** Resets the editor mode and refreshes terrain. */
	function resetMode() {
		controller.refreshTerrain();
		controller.reset();
	}

	/** Switches the editor to draw mode. */
	function drawMode() {
		controller.drawMode();
	}

	/** Switches the editor to waypoints mode. */
	function waypointsMode() {
		controller.waypointsMode(currentChosenWaypointsFaction);
	}

	/** Updates the waypoints to the webapi. */
	function confirmsWaypoints() {
		controller.updateWaypoint();
	}
</script>

{#snippet mapSvgSnippet()}
	<TerrainLayer terrainData={controller.terrainData} />
	<EditorTerrainLayer {controller} />
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	{#if controller.state.type == 'draw'}
		<path d={GetSmoothedClosedPath(controller.state.drawPolygon, 0.7)} class="draw-polygon" />
	{:else if controller.state.type == 'draw-waypoints'}
		{#each controller.state.waypoints.points as point}
			<circle r="5" cx={point.x} cy={point.y} fill="red" />
		{/each}
	{/if}
{/snippet}

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div onclick={handleClick} bind:this={clickTarget}>
	<SvgMap svgSnippet={mapSvgSnippet} bind:this={map} />
</div>

mode = {controller.state.type}
<button onclick={resetMode} style="margin-bottom: 1em;">Reset</button>
<button onclick={drawMode} style="margin-bottom: 1em;">Draw Mode</button>
<button onclick={waypointsMode} style="margin-bottom: 1em;">Waypoints Mode</button>

{#if controller.state.type == 'selected'}
	id = {controller.state.terrain.terrainId}
	x = <input type="number" class="number-input" bind:value={controller.state.terrain.position.x} />
	y = <input type="number" class="number-input" bind:value={controller.state.terrain.position.y} />
	degrees =
	<input type="number" class="number-input" bind:value={controller.state.terrain.degrees} />
{:else if controller.state.type == 'draw-waypoints'}
	<select bind:value={currentChosenWaypointsFaction}>
		<option value="BLUE">BLUE</option>
		<option value="RED">RED</option>
	</select>
	<button onclick={confirmsWaypoints} style="margin-bottom: 1em;">Confirm</button>
{/if}

<style lang="less">
	@stroke-width: 1;
	.number-input {
		width: 4em;
	}
	.draw-polygon {
		fill: #d2aed588;
		stroke: #c2a0cc;
		stroke-width: @stroke-width;
	}
</style>
