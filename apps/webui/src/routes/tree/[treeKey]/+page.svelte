<script lang="ts">
	import { page } from '$app/state';
	import {
		loadTreeLocal,
		type TreeInspectionSave as GameTreeInspectionSave
	} from '$lib/scenes-storage';
	import { onMount } from 'svelte';
	import ExpectimaxTreeNode from './expectimax-tree-node.svelte';
	import MctsTreeNode from './mcts-tree-node.svelte';
	import MinimaxTreeNode from './minimax-tree-node.svelte';

	let treeSave: GameTreeInspectionSave | null = $state(null);

	onMount(async () => {
		const treeKey = page.params['treeKey'] as string;
		treeSave = await loadTreeLocal(treeKey);
	});
</script>

<svelte:head>
	<title>Game tree</title>
</svelte:head>

<h1>Game tree</h1>

{#if treeSave}
	<span>Best action</span>
	<pre><code>{JSON.stringify(treeSave.gameTree.bestAction, null, 2)}</code
		></pre>
	<span>Root Node</span>
	{#if treeSave.gameTree.type === 'MctsTreeInspectionModel'}
		<MctsTreeNode
			node={treeSave.gameTree.treeRoot}
			mapData={treeSave.mapData}
		/>
	{:else if treeSave.gameTree.type === 'MinimaxTreeInspectionModel'}
		<MinimaxTreeNode
			node={treeSave.gameTree.treeRoot}
			mapData={treeSave.mapData}
		/>
	{:else if treeSave.gameTree.type === 'ExpectimaxTreeInspectionModel'}
		<ExpectimaxTreeNode
			node={treeSave.gameTree.treeRoot}
			mapData={treeSave.mapData}
		/>
	{/if}
{/if}
