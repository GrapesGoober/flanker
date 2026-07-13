<script lang="ts">
	import { GetGameStateJSON, PutGameStateJSON } from '$lib/api';

	let scene: string = $state('');
	let sceneName: string = $state('');
	let gameId: number = $state(0);

	async function GetGameState() {
		scene = await GetGameStateJSON(sceneName, gameId);
	}
	async function PutGameState() {
		await PutGameStateJSON(sceneName, gameId, scene);
	}
</script>

scene data = {scene}
Scene Name: <input type="text" bind:value={sceneName} />
Game ID: <input type="number" bind:value={gameId} />
<input type="button" value="Get Scene" onclick={GetGameState} />
<input type="button" value="Set Scene" onclick={PutGameState} />
