<script lang="ts">
	import { page } from '$app/state';
	import {
		GetMapData,
		type GameTreeInspection,
		type MapViewState
	} from '$lib/api';
	import { loadGameLocal, loadTreeLocal } from '$lib/scenes-storage';
	import { onMount } from 'svelte';
	import TreeNode from './tree-node.svelte';

	let gameTree: GameTreeInspection | null = $state(null);
	let mapData: MapViewState = $state({ terrains: [], boundary: [] });

	onMount(async () => {
		const gameKey = page.params['gameKey'] as string;
		const treeKey = page.params['treeKey'] as string;
		mapData = await GetMapData(loadGameLocal(gameKey));
		gameTree = loadTreeLocal(gameKey, treeKey);
	});
</script>

<svelte:head>
	<title>Game tree</title>
</svelte:head>

<h1>Game tree</h1>

{#if gameTree}
	{#if gameTree.type === 'MctsTreeInspection'}
		<p>Best action</p>
		<pre><code>{JSON.stringify(gameTree.bestAction, null, 2)}</code></pre>
		<TreeNode node={gameTree.treeRoot} action={null} {mapData} />
	{:else}
		<p>Whoops, only MCTS tree supported.</p>
	{/if}
{/if}
