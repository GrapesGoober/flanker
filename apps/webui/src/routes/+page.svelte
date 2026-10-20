<script lang="ts">
	import { ExceptionProxy } from '$lib/exception-proxy';
	import { onMount } from 'svelte';
	import { GameSavesController } from './game-saves-controller.svelte';

	const gameSavesController = ExceptionProxy.wrap(new GameSavesController());
	let controller: GameSavesController = $state(gameSavesController);

	let selectedScenes: string[] = $state([]);
	let newGameName: string = $state('');
	let newQuickAccessName: string = $state('');
	let newQuickAccessSceneNames: string[] = $state([]);

	onMount(() => {
		controller.reloadList();
	});

	$effect(() => {
		newGameName = selectedScenes.join('-');
	});

	function addQuickAccess() {
		if (newQuickAccessName.trim().length === 0) {
			alert('Quick access name is required');
			return;
		}
		if (newQuickAccessSceneNames.length === 0) {
			alert('Select at least one scene');
			return;
		}

		controller.addQuickAccess(newQuickAccessName, newQuickAccessSceneNames);
		newQuickAccessName = '';
		newQuickAccessSceneNames = [];
	}

	async function createNewGameFromSelection() {
		if (selectedScenes.length == 0) return;
		controller.createNewGame(selectedScenes, newGameName);
	}

	function deleteQuickAccess(quickAccessName: string) {
		if (confirm(`Confirm delete quick access ${quickAccessName}?`)) {
			controller.deleteQuickAccess(quickAccessName);
		}
	}

	function deleteGameSave(gameKey: string) {
		if (confirm(`Confirm delete save ${gameKey}?`)) {
			controller.deleteGameSave(gameKey);
		}
	}

	function renameGameSave(gameKey: string) {
		const newGameKey = prompt(`Rename save ${gameKey} as:`, gameKey)?.trim();
		if (!newGameKey) return null;
		controller.renameGameSave(gameKey, newGameKey);
	}
</script>

<h1>Project Flanker</h1>

<h3>Game Saves</h3>
{#if controller.saveGameKeys.length === 0}
	<p>No game saves found.</p>
{:else}
	<ul>
		{#each controller.saveGameKeys as gameKey}
			<li>
				<details>
					<summary>
						{gameKey}
					</summary>
					<ul>
						<li>
							<input
								type="button"
								value="Game Page"
								onclick={() => window.open(`/${gameKey}/game`)}
							/>
							<input
								type="button"
								value="Logs Page"
								onclick={() => window.open(`/${gameKey}/logs`)}
							/>
							<input
								type="button"
								value="Inspect"
								onclick={() => window.open(`/${gameKey}/inspect`)}
							/>
							<input
								type="button"
								value="Inspect Tree"
								onclick={() => window.open(`/${gameKey}/inspect-tree`)}
							/>
						</li>
						<li>
							<input
								type="button"
								value="Get AI Match Result"
								onclick={() => controller.createAiMatchSave(gameKey)}
							/>
						</li>
						<li>
							<input
								type="button"
								value="Rename"
								onclick={() => renameGameSave(gameKey)}
							/>

							<input
								type="button"
								value="Duplicate"
								onclick={() => controller.duplicateGameSave(gameKey)}
							/>
						</li>
						<li>
							<input
								type="button"
								value="Copy JSON"
								onclick={() => controller.copyGameSaveJson(gameKey)}
							/>
							<input
								type="button"
								value="Copy JSON (string escaped)"
								onclick={() => controller.copyGameSaveJsonEscaped(gameKey)}
							/>
						</li>
						<li>
							<input
								type="button"
								value="❌"
								onclick={() => {
									deleteGameSave(gameKey);
								}}
							/>
						</li>
					</ul>
				</details>
			</li>
		{/each}
	</ul>
{/if}

<h3>Load From Quick Access</h3>

{#if controller.quickAccesses.length === 0}
	<p>No quick access.</p>
{:else}
	<ul>
		{#each controller.quickAccesses as quickAccess}
			<li>
				<input
					type="button"
					value={quickAccess.quickAccessName}
					onclick={() => {
						controller.createNewFromQuickAccess(quickAccess);
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

<details class="collapsible-section">
	<summary>
		<span>Add Quick Access</span>
	</summary>

	<div class="collapsible-content">
		<input
			type="text"
			placeholder="Quick access name"
			bind:value={newQuickAccessName}
		/>

		{#if controller.sceneManifest.sceneNames.length === 0}
			<p>No scenes available to add.</p>
		{:else}
			<ul>
				{#each controller.sceneManifest.sceneNames as sceneName}
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
	</div>
</details>

<details class="collapsible-section">
	<summary>
		<span>Load From Each Scenes</span>
	</summary>

	<div class="collapsible-content">
		{#if controller.sceneManifest.sceneNames.length === 0}
			<p>No scenes.</p>
		{:else}
			<ul>
				{#each controller.sceneManifest.sceneNames as sceneName}
					<li>
						<input
							type="checkbox"
							value={sceneName}
							bind:group={selectedScenes}
						/>
						{sceneName}
					</li>
				{/each}
			</ul>
		{/if}

		<input type="text" bind:value={newGameName} />
		<input
			type="button"
			value="New Game"
			onclick={createNewGameFromSelection}
		/>
	</div>
</details>

<style>
	.collapsible-section {
		margin-bottom: 1rem;
	}

	.collapsible-content {
		padding: 0.75rem 0 0;
	}
</style>
