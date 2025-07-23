<script lang="ts">
	import { onMount } from 'svelte';
	import { getTerrainData, type TerrainFeatureData, type Vec2 } from '$lib';
	import SvgMap from '$lib/map/svg-map.svelte';

	let map: SvgMap | null = $state(null);
	let terrainData: TerrainFeatureData[] = $state([]);
	let coords: Vec2[] = $state([]);

	onMount(async () => {
		terrainData = await getTerrainData();
	});

	function AddVertex(event: MouseEvent) {
		if (map == null) {
			return;
		}
		let worldPos: Vec2 = map.ToWorldCoords({ x: event.clientX, y: event.clientY });
		coords.push(worldPos);
	}

	function ToSvgString(coords: { x: number; y: number }[]): string {
		return coords.map((point) => `${point.x},${point.y}`).join(' ');
	}
	function ToPythonListString(coords: Vec2[]): string {
		if (coords.length === 0) return 'pivot: Vec2(0, 0),\nvertices: []';
		const pivot = coords[0];
		if (pivot == undefined) {
			return '';
		}
		const pivotStr = `Vec2(${Math.round(pivot.x)}, ${Math.round(pivot.y)}),\n`;
		return (
			`pivot= ${pivotStr}` +
			'vertices= [\n' +
			coords
				.map((c) => `Vec2(${Math.round(c.x - pivot.x)}, ${Math.round(c.y - pivot.y)}),`)
				.join('\n') +
			'\n],'
		);
	}

	function refreshTerrainData() {
		coords = [];
		getTerrainData().then((data) => {
			terrainData = data;
		});
	}

	function copyToClipboard() {
		navigator.clipboard.writeText(ToPythonListString(coords));
	}
</script>

{#snippet mapSvgSnippet()}
	<polygon points={ToSvgString(coords)} class="editor" />
{/snippet}

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div onclick={AddVertex}>
	<SvgMap svgSnippet={mapSvgSnippet} {terrainData} bind:this={map} />
</div>

<button onclick={refreshTerrainData} style="margin-bottom: 1em;">Refresh</button>
<button onclick={copyToClipboard} style="margin-bottom: 1em;">Copy</button>

<textarea
	readonly
	style="width: 100%; min-height: 120px; resize: vertical; font-family: monospace; margin-top: 1em;"
	value={ToPythonListString(coords)}
></textarea>

<style lang="less">
	@stroke-width: 1;
	.editor {
		fill: #ccd5ae88;
		stroke: #c2cca0;
		stroke-width: @stroke-width;
	}
</style>
