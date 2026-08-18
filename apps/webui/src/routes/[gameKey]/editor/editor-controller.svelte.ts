import {
	AddTerrainData,
	DeleteTerrainData,
	GetTerrainData,
	GetUnitStatesData,
	UpdateTerrainData,
	UpdateWaypointsData,
	type AiWaypointsModel,
	type GameViewState,
	type TerrainModel,
	type TerrainType,
	type Vec2
} from '$lib/api';
import { transform } from '$lib/map-utils';
import { loadGameLocal, saveGameLocal } from '$lib/scenes-storage';
import { v4 as uuidv4 } from 'uuid';

type EditorControllerState =
	| { type: 'default' }
	| { type: 'selected'; terrain: TerrainModel }
	| { type: 'draw'; drawPolygon: Vec2[]; terrainType: TerrainType }
	| { type: 'draw-waypoints'; waypoints: AiWaypointsModel };

/**
 * Controller for managing terrain editing and polygon drawing in the editor.
 * Handles terrain data, selection, drawing mode, and state transitions.
 */
export class EditorController {
	terrainData: TerrainModel[] = $state([]);
	combatUnitsData: GameViewState = $state({
		objectiveState: 'INCOMPLETE',
		hasInitiative: false,
		squads: []
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
		this.terrainData = await GetTerrainData(gameStateJson);
		this.combatUnitsData = await GetUnitStatesData(gameStateJson);
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
	async selectTerrain(terrain: TerrainModel) {
		if (this.state.type != 'default' && this.state.type != 'selected') return;
		const gameStateJson = this.getGameStateJson();
		if (this.state.type == 'selected') {
			// Update the already selected terrain if selecting a new one.
			const viewState = await UpdateTerrainData(gameStateJson, this.state.terrain);
			this.updateGameStateJson(viewState.jsonState);
			await this.refreshData();
			const selectedTerrain = this.terrainData.find((i) => i.terrainId === terrain.terrainId);
			if (selectedTerrain != undefined) {
				this.state = {
					type: 'selected',
					terrain: selectedTerrain
				};
			}
		} else {
			this.state = {
				type: 'selected',
				terrain: terrain
			};
		}
	}

	/** Deletes the selected terrain */
	async deleteTerrain() {
		if (this.state.type != 'selected') return;
		const gameStateJson = this.getGameStateJson();
		const viewState = await DeleteTerrainData(gameStateJson, this.state.terrain.terrainId);
		this.updateGameStateJson(viewState.jsonState);
		await this.refreshData();
	}
	/** Asynchronously updates the selected terrain data via the API. */
	async updateTerrainAsync() {
		if (this.state.type != 'selected') return;
		const gameStateJson = this.getGameStateJson();
		const viewState = await UpdateTerrainData(gameStateJson, this.state.terrain);
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
		const viewState = await UpdateWaypointsData(gameStateJson, this.state.waypoints);
		this.updateGameStateJson(viewState.jsonState);
		await this.refreshData();
	}
}
