<script lang="ts">
	import { onMount } from 'svelte';
	import { SvgMap } from '$lib/components';
	import EditorTerrainLayer from './editor-terrain-layer.svelte';
	import { EditorController } from './editor-controller.svelte';
	import { GetSmoothedClosedPath } from '$lib/map-utils';
	import TerrainLayer from '$lib/components/terrain-layer.svelte';

	let controller: EditorController = $state(new EditorController());
	let map: SvgMap | null = $state(null);
	let clickTarget: HTMLElement | null = $state(null);

	onMount(() => {
		controller.refreshTerrain();
	});

	function addVertex(event: MouseEvent) {
		if (map == null) return;
		const node = clickTarget as HTMLElement;
		const rect = node.getBoundingClientRect();
		const x = event.clientX - rect.x;
		const y = event.clientY - rect.y;
		let worldPos = map.ToWorldCoords({ x, y });
		controller.addVertex(worldPos);
	}

	function resetMode() {
		controller.refreshTerrain();
		controller.reset();
	}

	function drawMode() {
		controller.drawMode();
	}
</script>

{#snippet mapSvgSnippet()}
	<TerrainLayer terrainData={controller.terrainData} />
	<EditorTerrainLayer {controller} />
	{#if controller.state.type == 'draw'}
		<path d={GetSmoothedClosedPath(controller.state.drawPolygon, 0.7)} class="draw-polygon" />
	{/if}
{/snippet}

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div onclick={addVertex} bind:this={clickTarget}>
	<SvgMap svgSnippet={mapSvgSnippet} bind:this={map} />
</div>

mode = {controller.state.type}
<button onclick={resetMode} style="margin-bottom: 1em;">Reset</button>
<button onclick={drawMode} style="margin-bottom: 1em;">Draw Mode</button>

{#if controller.state.type == 'selected'}
	id = {controller.state.terrain.terrainId}
	x = <input type="number" class="number-input" bind:value={controller.state.terrain.position.x} />
	y = <input type="number" class="number-input" bind:value={controller.state.terrain.position.y} />
	degrees =
	<input type="number" class="number-input" bind:value={controller.state.terrain.degrees} />
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
