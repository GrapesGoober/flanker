import { GetTerrainData, UpdateTerrainData, type TerrainModel, type Vec2 } from '$lib';

type EditorControllerState =
	| { type: 'default' }
	| { type: 'selected'; terrain: TerrainModel }
	| { type: 'draw'; drawPolygon: Vec2[] };

export class EditorController {
	terrainData: TerrainModel[] = $state([]);
	state: EditorControllerState = $state({ type: 'default' });

	refreshTerrain() {
		GetTerrainData().then((data) => {
			this.terrainData = data;
		});
	}
	addVertex(worldPos: Vec2) {
		if (this.state.type != 'draw') return;
		this.state.drawPolygon.push(worldPos);
	}
	selectTerrain(terrain: TerrainModel) {
		if (this.state.type != 'default' && this.state.type != 'selected') return;
		if (this.state.type == 'selected') UpdateTerrainData(this.state.terrain);
		this.state = {
			type: 'selected',
			terrain: terrain
		};
	}
	async updateTerrainAsync() {
		if (this.state.type != 'selected') return;
		await UpdateTerrainData(this.state.terrain);
	}
	reset() {
		this.state = { type: 'default' };
	}
	drawMode() {
		this.state = { type: 'draw', drawPolygon: [] };
	}
}
