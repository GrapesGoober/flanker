# Project Flanker

Flanker is a web-app strategy game adaptation of Arty Concliffe's **_Crossfire_**. This project is designed as an effort to digitize Crossfire, focusing on core gameplay mechanics rather than being a feature-complete standalone game.

## Getting Started

### Prerequisites

- Node.js and npm (for the `webui`)
- Python 3.11+ (for the `webapi` and `core`)
- Recommended: `pip` for Python dependencies

### Installation

- Install Python dependencies:
  ```
  pip install -r requirements.txt
  ```
- With vscode, you can set up pytest using `.vscode/settings.json`
  ```
  "python.testing.pytestEnabled": true,
  ```
  Or alternatively, run pytest manually in terminal
  ```
  python -m pytest
  ```
- With vscode, you can set up FastApi debugger using `.vscode/launch.json`. You can use your own port with `--port` argument.

  ```
  "name": "Python Debugger: FastAPI",
  "type": "debugpy",
  "request": "launch",
  "module": "uvicorn",
  "args": ["webapi:app", "--reload"],
  "jinja": true
  ```

- Install Node.js dependencies:
  ```
  cd webui
  npm install
  ```
- Add environment variable file to `/webui/.env`. For `VITE_WEBAPI_URL`, use the same URL that the FastApi app is using; the default is `localhost:8000`. For `VITE_PORT`, this configures the port number for webui's VITE app. Use whichever port you prefer. The default is `5173`.
  ```
  # Note: "VITE_" prefix is required
  VITE_WEBAPI_URL=http://localhost:8000
  VITE_PORT=5173
  ```

## Running App

- Start the webapi server `http://localhost:8000`. Either use the vscode debugger to run fastapi, or run this command in terminal. You can use your own port with `--port` argument.
  ```
  fastapi dev webapi
  ```
- Run the webui development server and open the app in your browser, `http://localhost:5173/`. Either use vscode debugger or run this in terminal
  ```
  cd webui
  npm run dev
  ```
  Or expose to local network
  ```
  cd webui
  npm run dev-expose
  ```

## Project Structure

### `webui/`

Svelte-based web frontend for the game.

- This is the presentation (view) layer of the game. This is strictly for user interface and game visualization logic. No gameplay level logic implemented here.
- Svelte app Vite for development and build. Contains Svelte components, routes, and static assets.
- Uses `openapi-ts` and `openapi-fetch` from webapi's OpenApi schema.

### `webapi/`

Python FastApi app serving the game logic and running the scenes. The game rules are not intended to be implemented here, only exposed.

- This is the service layer coordinating the actions, AI, combat units, terrain, and scenes.
- Defines API models and manages the game state.
- Intended to be run as an API or service for the webui. This bridges the gap between presentation layer and the core's actions.

### `core/`

- Core game engine logic in Python. The is the domain level gameplay logic implemented in ECS. The components (data models) and systems are defined here.
- Contains `GameState` object for ECS architecture. Here implements the entities table and various operations to the game state.
- Implements systems for gameplay logic: commands, factions, fire, movement, line-of-sight. Contains reusable components and utility functions. These systems and utils are implemented as static methods. Some system methods represent player actions, while some other represent other non-action mechanics.
- Includes a `tests/` directory with unit tests for core systems and actions.
