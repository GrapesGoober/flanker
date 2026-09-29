<script lang="ts">
	import { page } from '$app/state';
	import {
		BorderFriendlyUnit,
		BorderHostileUnit,
		RifleSquad,
		SvgMap,
		TerrainLayer
	} from '$lib/components';
	import { ExceptionProxy } from '$lib/exception-proxy';
	import { GetSmoothedClosedPath } from '$lib/map-utils';
	import { onMount } from 'svelte';
	import { EditorController } from './editor-controller.svelte';
	import EditorOverlay from './editor-overlay.svelte';

	const editorController = ExceptionProxy.wrap(new EditorController());
	let controller: EditorController = $state(editorController);
	let map: SvgMap | null = $state(null);
	let clickTarget: HTMLElement | null = $state(null);

	/// Refreshes terrain data when the component mounts. */
	onMount(() => {
		const gameKey: string = page.params['gameKey'] as string;
		controller.initialize(gameKey);
		controller.refreshData();
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

	function resetMode() {
		controller.refreshData();
		controller.reset();
	}

	function drawMode() {
		controller.drawMode();
	}

	async function deleteTerrain() {
		await controller.deleteTerrainAsync();
		resetMode();
	}

	async function updateTerrain() {
		await controller.updateTerrainAsync();
		resetMode();
	}

	async function updateUnit() {
		await controller.updateUnitAsync();
		resetMode();
	}

	function waypointsMode() {
		controller.waypointsMode('RED');
	}

	function confirmsWaypoints() {
		controller.updateWaypoint();
	}
	async function finishDraw() {
		await controller.finishDraw();
	}

	function selectUnit(unitId: string, event: MouseEvent) {
		event.stopPropagation(); // Prevent the terrain's onclick trigger
		controller.selectUnit(unitId);
	}
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
{#snippet mapSvgSnippet()}
	<!-- Draw the base terrains and units -->
	<TerrainLayer mapData={controller.mapData} />
	<svg overflow="visible" class="transparent-icons">
		{#if controller.state.type === 'selected-unit'}
			{@const selectedUnit = controller.state.unit}
			{@const position = controller.state.unit.position}

			{#if selectedUnit.isFriendly}
				<g transform="translate({position.x}, {position.y})"
					><BorderFriendlyUnit /></g
				>
			{:else if !selectedUnit.isFriendly}
				<g transform="translate({position.x}, {position.y})"
					><BorderHostileUnit /></g
				>
			{/if}
		{/if}
	</svg>
	{#each controller.viewState.squads as unit, index}
		{#if controller.viewState.squads[index] != undefined}
			<g onclick={(event) => selectUnit(unit.unitId, event)}>
				<RifleSquad bind:rifleSquadData={controller.viewState.squads[index]} />
			</g>
		{/if}
	{/each}
	<!-- Draw the overlay on top -->
	<EditorOverlay {controller} />

	<!-- Draw the purple drawing mode UIs -->
	{#if controller.state.type == 'draw'}
		<path
			d={GetSmoothedClosedPath(controller.state.drawPolygon, 0.7)}
			class="draw-polygon"
		/>
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
<button onclick={waypointsMode} style="margin-bottom: 1em;"
	>Waypoints Mode</button
>

{#if controller.state.type == 'selected-terrain'}
	id = {controller.state.terrain.terrainId}
	x =
	<input
		type="number"
		class="number-input"
		bind:value={controller.state.terrain.position.x}
	/>
	y =
	<input
		type="number"
		class="number-input"
		bind:value={controller.state.terrain.position.y}
	/>
	degrees =
	<input
		type="number"
		class="number-input"
		bind:value={controller.state.terrain.degrees}
	/>
	<button onclick={deleteTerrain} style="margin-bottom: 1em;"
		>Delete Terrain</button
	>
	<button onclick={updateTerrain} style="margin-bottom: 1em;"
		>Update Terrain Changes</button
	>
{:else if controller.state.type == 'selected-unit'}
	id = {controller.state.unit.unitId}
	x =
	<input
		type="number"
		class="number-input"
		bind:value={controller.state.unit.position.x}
	/>
	y =
	<input
		type="number"
		class="number-input"
		bind:value={controller.state.unit.position.y}
	/>
	degrees =
	<input
		type="number"
		class="number-input"
		bind:value={controller.state.unit.degrees}
	/>
	fov =
	<input
		type="number"
		class="number-input"
		bind:value={controller.state.unit.fovDegrees}
	/>
	<select bind:value={controller.state.unit.isFriendly}>
		<option value={true}>BLUE</option>
		<option value={false}>RED</option>
	</select>

	<button onclick={updateUnit} style="margin-bottom: 1em;"
		>Update Unit Changes</button
	>
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
	<button onclick={confirmsWaypoints} style="margin-bottom: 1em;"
		>Confirm</button
	>
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
	.transparent-icons {
		opacity: 0.5;
	}
</style>
