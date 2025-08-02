import {
	getTerrainData,
	getTerrainTransformData,
	updateTerrainTransformData,
	type TerrainFeatureData,
	type TerrainTransformData,
	type Vec2
} from '$lib';

type EditorControllerState =
	| { type: 'default' }
	| { type: 'selected'; terrain: TerrainFeatureData; transform: TerrainTransformData }
	| { type: 'draw'; drawPolygon: Vec2[] };

export class EditorController {
	terrainData: TerrainFeatureData[] = $state([]);
	terrainTransformData: TerrainTransformData[] = $state([]);
	state: EditorControllerState = $state({ type: 'default' });

	refreshTerrain() {
		getTerrainData().then((data) => {
			this.terrainData = data;
		});
		getTerrainTransformData().then((data) => {
			this.terrainTransformData = data;
		});
	}
	addVertex(worldPos: Vec2) {
		if (this.state.type != 'draw') return;
		this.state.drawPolygon.push(worldPos);
	}
	selectTerrain(terrain: TerrainFeatureData) {
		if (this.state.type != 'default' && this.state.type != 'selected') return;
		let transform = this.terrainTransformData.find(
			(transform) => transform.feature_id == terrain.feature_id
		);
		if (transform == undefined)
			throw Error(`Terrain transform for id ${terrain.feature_id} not found`);
		this.state = {
			type: 'selected',
			terrain: terrain,
			transform: transform
		};
	}
	async updateTransformAsync() {
		if (this.state.type != 'selected') return;
		await updateTerrainTransformData(this.state.transform);
	}
	reset() {
		this.state = { type: 'default' };
	}
	drawMode() {
		this.state = { type: 'draw', drawPolygon: [] };
	}
}
