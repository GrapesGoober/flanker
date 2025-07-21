<script lang="ts">
	import { GetTerrainData, type TerrainFeatureData } from '$lib';
	import FriendlyRifleSquad from '$lib/svg-icons/friendly-rifle-squad.svelte';
	import HostileRifleSquad from '$lib/svg-icons/hostile-rifle-squad.svelte';
	import SvgMapNew from '$lib/svg-map-new.svelte';
	import { onMount } from 'svelte';

	let terrainData: TerrainFeatureData[] = $state([]);
	onMount(async () => {
		terrainData = await GetTerrainData();
	});
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
{/snippet}

<SvgMapNew svgSnippet={mapSvgSnippet} {terrainData}></SvgMapNew>
