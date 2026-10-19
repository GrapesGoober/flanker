<script lang="ts">
	import { page } from '$app/state';
	import {
		GetMapData,
		type GameTreeInspection,
		type MapViewState
	} from '$lib/api';
	import { loadGameLocal, loadTreeLocal } from '$lib/scenes-storage';
	import { onMount } from 'svelte';
	import ExpectimaxTreeNode from './expectimax-tree-node.svelte';
	import MctsTreeNode from './mcts-tree-node.svelte';
	import MinimaxTreeNode from './minimax-tree-node.svelte';

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
	<span>Best action</span>
	<pre><code>{JSON.stringify(gameTree.bestAction, null, 2)}</code></pre>
	<span>Root Node</span>
	{#if gameTree.type === 'MctsTreeInspection'}
		<MctsTreeNode node={gameTree.treeRoot} {mapData} />
	{:else if gameTree.type === 'MinimaxTreeInspection'}
		<MinimaxTreeNode node={gameTree.treeRoot} {mapData} />
	{:else}
		<ExpectimaxTreeNode node={gameTree.treeRoot} {mapData} />
	{/if}
{/if}
