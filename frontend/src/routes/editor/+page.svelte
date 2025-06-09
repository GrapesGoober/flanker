<script lang="ts">
	import { onMount } from 'svelte';
	import {
		GetTerrainData,
		GetRifleSquadsData,
		type RifleSquadData,
		type TerrainFeatureData
	} from '$lib';
	import Map from '$lib/map.svelte';

	type MapProps = {
		terrainData: TerrainFeatureData[];
		unitData: RifleSquadData[];
	};

	let mapProps: MapProps = $state({
		terrainData: [],
		unitData: []
	});

	onMount(async () => {
		mapProps.terrainData = await GetTerrainData();
		mapProps.unitData = await GetRifleSquadsData();
	});
</script>

<Map bind:props={mapProps}></Map>
