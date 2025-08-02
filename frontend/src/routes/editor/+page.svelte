<script lang="ts">
	import { onMount } from 'svelte';
	import SvgMap from '$lib/map/svg-map.svelte';
	import EditorTerrainFeatures from './editor-terrain-features.svelte';
	import { EditorController } from './editor-controller.svelte';
	import { GetSmoothedClosedPath } from '$lib/map/map-utils';

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

	function moveUp() {
		if (controller.state.type == 'selected') {
			let transform = controller.state.transform;
			transform.position.y -= 1;

			let coords = controller.state.terrain.coordinates;
			for (let i = 0; i < coords.length; i++) {
				coords[i]!.y -= 1;
			}
		}
	}

	function save() {
		controller.updateTransformAsync();
	}
</script>

{#snippet mapSvgSnippet()}
	<EditorTerrainFeatures {controller} />
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
<button onclick={moveUp} style="margin-bottom: 1em;">MoveUp</button>
<button onclick={save} style="margin-bottom: 1em;">Save</button>

<style lang="less">
	@stroke-width: 1;
	.draw-polygon {
		fill: #ccd5ae88;
		stroke: #c2cca0;
		stroke-width: @stroke-width;
	}
</style>
