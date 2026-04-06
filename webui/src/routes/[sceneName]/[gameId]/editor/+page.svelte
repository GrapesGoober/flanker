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

	/// Refreshes terrain data when the component mounts. */
	onMount(() => {
		void controller.refreshTerrain();
	});

	/** Handles click as adding a vertex or waypoint, depending on state. */
	function handleClick(event: MouseEvent) {
		if (map == null) return;
		if (controller.isFetching) return;
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
		void controller.refreshTerrain();
		controller.reset();
	}

	/** Switches the editor to draw mode. */
	function drawMode() {
		controller.drawMode();
	}

	/** Finishes the current draw and saves as terrain. */
	async function deleteTerrain() {
		await controller.deleteTerrain();
	}

	/** Switches the editor to waypoints mode. */
	function waypointsMode() {
		controller.waypointsMode('RED');
	}

	/** Updates the waypoints to the webapi. */
	async function confirmsWaypoints() {
		await controller.updateWaypoint();
	}
	/** Finishes the current draw and saves as terrain. */
	async function finishDraw() {
		await controller.finishDraw();
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

{#if controller.errorMessage}
	<div class="error-console">
		<div class="error-console-header">
			<span>Editor Error</span>
			<button onclick={() => controller.clearError()}>Dismiss</button>
		</div>
		<div class="error-console-current">{controller.errorMessage}</div>
		{#if controller.errorLog.length > 1}
			<div class="error-console-log">
				{#each controller.errorLog.slice(1) as entry}
					<div>{entry}</div>
				{/each}
			</div>
		{/if}
	</div>
{/if}

{#if controller.state.type == 'selected'}
	id = {controller.state.terrain.terrainId}
	x = <input type="number" class="number-input" bind:value={controller.state.terrain.position.x} />
	y = <input type="number" class="number-input" bind:value={controller.state.terrain.position.y} />
	degrees =
	<input type="number" class="number-input" bind:value={controller.state.terrain.degrees} />
	<button onclick={deleteTerrain} style="margin-bottom: 1em;">Delete Terrain</button>
{:else if controller.state.type == 'draw'}
	<select bind:value={controller.state.terrainType}>
		<option value="FOREST">FOREST</option>
		<option value="ROAD">ROAD</option>
		<option value="FIELD">FIELD</option>
		<option value="WATER">WATER</option>
		<option value="BUILDING">BUILDING</option>
	</select>

	<button onclick={finishDraw} style="margin-bottom: 1em;">Finish Draw</button>
{:else if controller.state.type == 'draw-waypoints'}
	length = {controller.state.waypoints.points.length}
	<select bind:value={controller.state.waypoints.faction}>
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
	.error-console {
		margin: 0.75rem 0;
		padding: 0.75rem;
		max-width: 42rem;
		border: 1px solid #8f2b2b;
		background-color: #fff0f0;
		color: #5a1111;
		font-family: monospace;
	}
	.error-console-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		font-weight: 700;
	}
	.error-console-current {
		margin-top: 0.5rem;
	}
	.error-console-log {
		margin-top: 0.5rem;
		max-height: 7rem;
		overflow: auto;
		font-size: 0.85rem;
	}
</style>
