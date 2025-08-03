import {
	getTerrainData,
	updateTerrainTransformData,
	type TerrainFeatureData,
	type Vec2
} from '$lib';

type EditorControllerState =
	| { type: 'default' }
	| { type: 'selected'; terrain: TerrainFeatureData }
	| { type: 'draw'; drawPolygon: Vec2[] };

export class EditorController {
	terrainData: TerrainFeatureData[] = $state([]);
	state: EditorControllerState = $state({ type: 'default' });

	refreshTerrain() {
		getTerrainData().then((data) => {
			this.terrainData = data;
		});
	}
	addVertex(worldPos: Vec2) {
		if (this.state.type != 'draw') return;
		this.state.drawPolygon.push(worldPos);
	}
	selectTerrain(terrain: TerrainFeatureData) {
		if (this.state.type != 'default' && this.state.type != 'selected') return;
		this.state = {
			type: 'selected',
			terrain: terrain
		};
	}
	async updateTransformAsync() {
		if (this.state.type != 'selected') return;
		await updateTerrainTransformData(this.state.terrain);
	}
	reset() {
		this.state = { type: 'default' };
	}
	drawMode() {
		this.state = { type: 'draw', drawPolygon: [] };
	}
}
