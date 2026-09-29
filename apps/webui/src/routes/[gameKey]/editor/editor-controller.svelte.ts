import {
	AddTerrainData,
	DeleteTerrainData,
	GetMapData,
	GetViewStatesData,
	UpdateTerrainData,
	UpdateUnit,
	UpdateWaypointsData,
	type AiWaypointsModel,
	type GameViewState,
	type MapViewState,
	type RifleSquadData,
	type TerrainModel,
	type TerrainType,
	type Vec2
} from '$lib/api';
import { transform } from '$lib/map-utils';
import { loadGameLocal, saveGameLocal } from '$lib/scenes-storage';
import { v4 as uuidv4 } from 'uuid';

type EditorControllerState =
	| { type: 'default' }
	| { type: 'selected-terrain'; terrain: TerrainModel }
	| { type: 'selected-unit'; unit: RifleSquadData }
	| { type: 'draw'; drawPolygon: Vec2[]; terrainType: TerrainType }
	| { type: 'draw-waypoints'; waypoints: AiWaypointsModel };

export class EditorController {
	mapData: MapViewState = $state({
		terrains: [],
		boundary: []
	});
	viewState: GameViewState = $state({
		objectiveState: 'INCOMPLETE',
		hasInitiative: false,
		squads: [],
		fireEffectPairs: []
	});
	state: EditorControllerState = $state({ type: 'default' });
	gameKey: string = $state('');

	getGameStateJson(): string {
		const gameStateJson = loadGameLocal(this.gameKey);
		return gameStateJson;
	}

	updateGameStateJson(gameStateJson: string) {
		saveGameLocal(this.gameKey, gameStateJson);
	}

	initialize(gameKey: string) {
		this.gameKey = gameKey;
	}

	/** Refreshes terrain data from the API. */
	async refreshData() {
		const gameStateJson = this.getGameStateJson();
		this.mapData = await GetMapData(gameStateJson);
		this.viewState = await GetViewStatesData(gameStateJson);
	}

	/** Resets the editor state to default. */
	reset() {
		this.state = { type: 'default' };
	}
	/** Switches the editor to draw mode and initializes a new polygon. */
	drawMode() {
		this.state = { type: 'draw', drawPolygon: [], terrainType: 'FOREST' };
	}
	/** Switches the editor to draw-waypoints mode and sets a new empty waypoints list. */
	waypointsMode(faction: 'BLUE' | 'RED') {
		this.state = { type: 'draw-waypoints', waypoints: { faction, points: [] } };
	}

	/** Adds a vertex to the current draw polygon if in draw mode. */
	addVertex(worldPos: Vec2) {
		if (this.state.type != 'draw') return;
		this.state.drawPolygon.push(worldPos);
	}
	/** Finishes the draw and saves the polygon as a new forest terrain. */
	async finishDraw() {
		if (this.state.type != 'draw' || this.state.drawPolygon.length < 3) return;
		const polygon = this.state.drawPolygon;
		const position = polygon[0]; // Assume first polygon as position
		if (position === undefined) return;
		const vertices = transform(polygon, { x: -position.x, y: -position.y }, 0);
		const terrain: TerrainModel = {
			// The ID is ignored as it will create a new one
			terrainId: uuidv4(),
			position: position,
			degrees: 0,
			vertices: vertices,
			terrainType: this.state.terrainType
		};
		const gameStateJson = this.getGameStateJson();
		const viewState = await AddTerrainData(gameStateJson, terrain);
		this.updateGameStateJson(viewState.jsonState);
		await this.refreshData();
		this.reset();
	}

	/** Selects a terrain object and updates its data if already selected. */
	selectTerrain(terrain: TerrainModel) {
		if (this.state.type != 'default') return;
		this.state = {
			type: 'selected-terrain',
			terrain: terrain
		};
	}

	/** Selects a combat unit for editing */
	selectUnit(unitId: string) {
		let unit = this.viewState.squads.find((squad) => squad.unitId == unitId);
		if (!unit) return;
		this.state = {
			type: 'selected-unit',
			unit: unit
		};
	}

	/** Async confirm changes to a combat unit and updates it via API */
	async updateUnitAsync() {
		if (this.state.type != 'selected-unit') return;
		const gameStateJson = this.getGameStateJson();
		const viewState = await UpdateUnit(gameStateJson, this.state.unit);
		this.updateGameStateJson(viewState.jsonState);
		await this.refreshData();
	}

	/** Deletes the selected terrain */
	async deleteTerrainAsync() {
		if (this.state.type != 'selected-terrain') return;
		const gameStateJson = this.getGameStateJson();
		const viewState = await DeleteTerrainData(
			gameStateJson,
			this.state.terrain.terrainId
		);
		this.updateGameStateJson(viewState.jsonState);
		await this.refreshData();
	}
	/** Asynchronously updates the selected terrain data via the API. */
	async updateTerrainAsync() {
		if (this.state.type != 'selected-terrain') return;
		const gameStateJson = this.getGameStateJson();
		const viewState = await UpdateTerrainData(
			gameStateJson,
			this.state.terrain
		);
		this.updateGameStateJson(viewState.jsonState);
		await this.refreshData();
	}

	/** Adds a new waypoint */
	addWaypoint(point: Vec2) {
		if (this.state.type != 'draw-waypoints') return;
		this.state.waypoints.points.push(point);
	}
	/** Async updates the waypoints to server */
	async updateWaypoint() {
		if (this.state.type != 'draw-waypoints') return;
		const gameStateJson = this.getGameStateJson();
		const viewState = await UpdateWaypointsData(
			gameStateJson,
			this.state.waypoints
		);
		this.updateGameStateJson(viewState.jsonState);
		await this.refreshData();
	}
}
