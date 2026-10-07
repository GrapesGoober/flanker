<script lang="ts">
	import {
		GetGameStateJSON,
		GetSceneNames,
		type SceneManifest
	} from '$lib/api';
	import {
		deleteGameLocal,
		getGameKeys,
		getQuickAccesses,
		saveGameLocal,
		setQuickAccesses,
		type QuickAccess
	} from '$lib/scenes-storage';
	import { onMount } from 'svelte';

	let saveGameKeys: string[] = $state([]);
	let sceneNames: SceneManifest = $state({
		sceneNames: []
	});
	let selectedScenes: string[] = $state([]);
	let newGameName: string = $state('');
	let quickAccesses: QuickAccess[] = $state([]);
	let newQuickAccessName: string = $state('');
	let newQuickAccessSceneNames: string[] = $state([]);

	onMount(reloadList);

	$effect(() => {
		newGameName = selectedScenes.join('-');
	});

	async function reloadList() {
		saveGameKeys = getGameKeys();
		sceneNames = await GetSceneNames();
		quickAccesses = getQuickAccesses();
	}

	function addQuickAccess() {
		const quickAccessName = newQuickAccessName.trim();
		const sceneNamesForQuickAccess = newQuickAccessSceneNames.slice();

		if (quickAccessName.length === 0) {
			alert('Quick access name is required');
			return;
		}
		if (sceneNamesForQuickAccess.length === 0) {
			alert('Select at least one scene');
			return;
		}
		if (
			quickAccesses.some((access) => access.quickAccessName === quickAccessName)
		) {
			alert('A quick access with this name already exists');
			return;
		}

		const newQuickAccess: QuickAccess = {
			quickAccessName,
			sceneNames: sceneNamesForQuickAccess
		};
		quickAccesses = [...quickAccesses, newQuickAccess];
		setQuickAccesses(quickAccesses);
		newQuickAccessName = '';
		newQuickAccessSceneNames = [];
	}

	async function createNewGameFromSelection() {
		if (selectedScenes.length == 0) return;
		const stateJson = await GetGameStateJSON(selectedScenes);
		saveGameLocal(newGameName, stateJson);
		reloadList();
	}

	async function createNewFromQuickAccess(quickAccessName: string) {
		const quickAccess = quickAccesses.find(
			(access) => access.quickAccessName === quickAccessName
		);
		const quickAccessSceneNames = quickAccess?.sceneNames ?? [];

		if (quickAccessSceneNames.length === 0) {
			alert('Cannot create a game from this quick access');
			return;
		}

		const stateJson = await GetGameStateJSON(quickAccessSceneNames);
		saveGameLocal(quickAccessName, stateJson);
		reloadList();
	}

	function deleteQuickAccess(quickAccessName: string) {
		if (confirm(`Confirm delete quick access ${quickAccessName}?`)) {
			quickAccesses = quickAccesses.filter(
				(access) => access.quickAccessName !== quickAccessName
			);
			setQuickAccesses(quickAccesses);
		}
	}

	function deleteGameSave(gameKey: string) {
		if (confirm(`Confirm delete save ${gameKey}?`)) {
			deleteGameLocal(gameKey);
			reloadList();
		}
	}
</script>

<h1>Project Flanker</h1>

<h3>Game Saves</h3>
{#if saveGameKeys.length === 0}
	<p>No game saves found.</p>
{:else}
	<ul>
		{#each saveGameKeys as gameKey}
			<li>
				<a href="/{gameKey}/game" class="key-link">
					<span class="key-text">{gameKey}</span>
				</a>
				<input
					type="button"
					value="❌"
					onclick={() => {
						deleteGameSave(gameKey);
					}}
				/>
			</li>
		{/each}
	</ul>
{/if}

<h3>Load From Quick Access</h3>

{#if quickAccesses.length === 0}
	<p>No quick access.</p>
{:else}
	<ul>
		{#each quickAccesses as quickAccess}
			<li>
				<input
					type="button"
					value={quickAccess.quickAccessName}
					onclick={() => {
						createNewFromQuickAccess(quickAccess.quickAccessName);
					}}
				/>
				<input
					type="button"
					value="❌"
					onclick={() => deleteQuickAccess(quickAccess.quickAccessName)}
				/>
			</li>
		{/each}
	</ul>
{/if}

<h3>Add Quick Access</h3>

<input
	type="text"
	placeholder="Quick access name"
	bind:value={newQuickAccessName}
/>

{#if sceneNames.sceneNames.length === 0}
	<p>No scenes available to add.</p>
{:else}
	<ul>
		{#each sceneNames.sceneNames as sceneName}
			<li>
				<input
					type="checkbox"
					value={sceneName}
					bind:group={newQuickAccessSceneNames}
				/>
				{sceneName}
			</li>
		{/each}
	</ul>
{/if}

<input type="button" value="Add Quick Access" onclick={addQuickAccess} />

<h3>Load From Each Scenes</h3>

{#if sceneNames.sceneNames.length === 0}
	<p>No scenes.</p>
{:else}
	<ul>
		{#each sceneNames.sceneNames as sceneName}
			<li>
				<input type="checkbox" value={sceneName} bind:group={selectedScenes} />
				{sceneName}
			</li>
		{/each}
	</ul>
{/if}

<input type="text" bind:value={newGameName} />
<input type="button" value="New Game" onclick={createNewGameFromSelection} />
