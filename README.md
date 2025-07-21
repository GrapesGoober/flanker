# Project Flanker

Flanker is a web-app strategy game adaptation of Arty Concliffe's **_Crossfire_**. This project is designed as an effort to digitize Crossfire, focusing on core gameplay mechanics rather than being a feature-complete standalone game.

## Getting Started

### Prerequisites

- Node.js and npm (for the frontend)
- Python 3.11+ (for the backend and core)
- Recommended: `pip` for Python dependencies

### Installation

- Install Python dependencies:
  ```
  pip install -r requirements.txt
  ```
- With vscode, you can set up pytest using `.vscode/settings.json`
  ```
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["core/tests", "--color=yes"],
  ```
  Or alternatively, run pytest manually in terminal
  ```
  python -m pytest core/tests
  ```
- With vscode, you can set up FastApi debugger using `.vscode/launch.json`

  ```
  "name": "Python Debugger: FastAPI",
  "type": "debugpy",
  "request": "launch",
  "module": "uvicorn",
  "args": ["backend:app", "--reload"],
  "jinja": true
  ```

- Install Node.js dependencies:
  ```
  cd frontend
  npm install
  ```

## Running App

- Start the backend server `http://127.0.0.1:8000`. Either use the vscode debugger to run fastapi, or run this command in terminal
  ```
  fastapi dev backend
  ```
- Run the frontend development server and open the app in your browser, `http://localhost:5173/`. Either use vscode debugger or run this in terminal
  ```
  cd frontend
  npm run dev
  ```
  Or expose to local network
  ```
  cd frontend
  npm run dev-expose
  ```

## Project Structure

### `frontend/`

Svelte-based web frontend for the game.

- This is the presentation (view) layer of the game. This is strictly for user interface and game visualization logic. No gameplay level logic implemented here.
- Svelte app Vite for development and build. Contains Svelte components, routes, and static assets.
- Uses `openapi-ts` and `openapi-fetch` from backend's OpenApi schema.

### `backend/`

Python FastApi backend implementing game logic and controllers.

- This is the presentation (view) layer and the controllers for actions, AI, combat units, terrain, and scenes.
- Defines API models and manages the game state.
- Intended to be run as an API or service for the frontend. This bridges the gap between presentation layer and the core's actions.

### `core/`

- Core game engine logic in Python. The is the domain level gameplay logic implemented in ECS. The components (data models) and systems are defined here.
- Contains `GameState` object for ECS architecture.
- Implements systems for gameplay logic: commands, factions, fire, movement, line-of-sight. Contains reusable components and utility functions. These systems and utils are implemented as static methods. Some system methods represent player actions, while some other represent other non-action mechanics.
- Includes a `tests/` directory with unit tests for core systems and actions.
