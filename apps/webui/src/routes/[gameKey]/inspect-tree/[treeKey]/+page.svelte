<script lang="ts">
	import { page } from '$app/state';
	import { GetMapData, type MapViewState, type MctsGameTreeInspection } from '$lib/api';
	import { loadGameLocal, loadTreeLocal } from '$lib/scenes-storage';
	import { onMount } from 'svelte';
	import TreeNode from './tree-node.svelte';

	let inspection: MctsGameTreeInspection | null = $state(null);
	let mapData: MapViewState = $state({ terrains: [], boundary: [] });

	onMount(async () => {
		const gameKey = page.params['gameKey'] as string;
		const treeKey = page.params['treeKey'] as string;
		mapData = await GetMapData(loadGameLocal(gameKey));
		inspection = JSON.parse(
			loadTreeLocal(gameKey, treeKey)
		) as MctsGameTreeInspection;
	});
</script>

<svelte:head>
	<title>Game tree</title>
</svelte:head>

<h1>Game tree</h1>

{#if inspection}
	<p>Best action</p>
	<pre><code>{JSON.stringify(inspection.bestAction, null, 2)}</code></pre>
	<TreeNode node={inspection.treeRoot} action={null} {mapData} />
{/if}
