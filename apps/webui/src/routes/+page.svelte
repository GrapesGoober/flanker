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

	onMount(async () => {
		await controller.reloadList();
	});

	$effect(() => {
		newGameName = selectedScenes.join('-');
	});

	async function addQuickAccess() {
		await controller.addQuickAccess(
			newQuickAccessName,
			newQuickAccessSceneNames
		);
		newQuickAccessName = '';
		newQuickAccessSceneNames = [];
	}

	async function createNewGameFromSelection() {
		if (selectedScenes.length == 0) return;
		controller.createNewGame(selectedScenes, newGameName);
	}

	async function deleteQuickAccess(quickAccessName: string) {
		if (confirm(`Confirm delete quick access ${quickAccessName}?`)) {
			await controller.deleteQuickAccess(quickAccessName);
		}
	}

	async function deleteGameSave(gameKey: string) {
		if (confirm(`Confirm delete save ${gameKey}?`)) {
			await controller.deleteGameSave(gameKey);
		}
	}

	function renameGameSave(gameKey: string) {
		const newGameKey = prompt(`Rename save ${gameKey} as:`, gameKey)?.trim();
		if (!newGameKey) return null;
		controller.renameGameSave(gameKey, newGameKey);
	}

	async function deleteTree(treeName: string) {
		if (confirm(`Confirm delete tree ${treeName}?`)) {
			controller.deleteTree(treeName);
		}
	}
</script>

<h1>Project Flanker</h1>

<fieldset
	disabled={controller.state.type === 'fetching'}
	inert={controller.state.type === 'fetching'}
>
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
								<a href={`/${gameKey}/game`}>Game Page</a>
								&nbsp;
								<a href={`/${gameKey}/logs`}>Logs Page</a>
								&nbsp;
								<a href={`/${gameKey}/inspect`}>Inspect</a>
								&nbsp;
							</li>
							<li>
								<input
									type="button"
									value="Get AI Match Result"
									onclick={() => controller.createAiMatchSave(gameKey)}
								/>
								<input
									type="button"
									value="Get Tree Inspection"
									onclick={() => controller.createTree(gameKey)}
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
									onclick={async () => {
										await deleteGameSave(gameKey);
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

	<h3>Game Trees</h3>

	{#if controller.treeNames.length === 0}
		<p>No saved trees for this game.</p>
	{:else}
		<ul>
			{#each controller.treeNames as treeName}
				<li>
					<a href="/tree/{encodeURIComponent(treeName)}">
						{treeName}
					</a>
					<input
						type="button"
						value="❌"
						onclick={() => deleteTree(treeName)}
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
</fieldset>

<style>
	fieldset {
		border: 0;
		margin: 0;
		min-width: 0;
		padding: 0;
	}

	.collapsible-section {
		margin-bottom: 1rem;
	}

	.collapsible-content {
		padding: 0.75rem 0 0;
	}
</style>
