<script lang="ts">
	import { GetTerrainData, type TerrainFeatureData, type Vec2 } from '$lib';
	import FriendlyRifleSquad from '$lib/svg-icons/friendly-rifle-squad.svelte';
	import HostileRifleSquad from '$lib/svg-icons/hostile-rifle-squad.svelte';
	import SvgMapNew from '$lib/svg-map-new.svelte';
	import { onMount } from 'svelte';

	let map: SvgMapNew | null = $state(null);
	let terrainData: TerrainFeatureData[] = $state([]);
	onMount(async () => {
		terrainData = await GetTerrainData();
	});

	let marker: Vec2 | null = $state(null);
	function OnClick(event: MouseEvent) {
		if (map == undefined) {
			return;
		}
		marker = map.ToWorldCoords({ x: event.clientX, y: event.clientY });
	}
</script>

{#snippet mapSvgSnippet()}
	<g transform="translate({30},{25})">
		<FriendlyRifleSquad />
		<foreignObject width="100" height="100">
			<p>PLT 1</p>
		</foreignObject>
	</g>

	<g transform="translate({80},{25})">
		<HostileRifleSquad />
	</g>

	{#if marker}
		<circle cx={marker.x - 5} cy={marker.y - 5} r="5" fill="red" />
	{/if}
{/snippet}

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div onclick={OnClick}>
	<SvgMapNew svgSnippet={mapSvgSnippet} {terrainData} bind:this={map} />
</div>
