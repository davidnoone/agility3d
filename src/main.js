import { loadPyodide } from
    "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide.mjs";

import * as THREE from
    "https://cdn.jsdelivr.net/npm/three@0.180.0/build/three.module.js";


const status = document.getElementById("status");


// ------------------------------------------------------------
// Three.js renderer
// ------------------------------------------------------------

const canvas = document.getElementById("game");

const renderer = new THREE.WebGLRenderer({
    canvas: canvas,
    antialias: true
});

renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(window.innerWidth, window.innerHeight);


const scene = new THREE.Scene();

scene.background = new THREE.Color(0x202020);


const camera = new THREE.PerspectiveCamera(
    60,
    window.innerWidth / window.innerHeight,
    0.1,
    100
);

camera.position.set(0, 0, 5);


// Cube
const geometry = new THREE.BoxGeometry(2, 2, 2);
const material = new THREE.MeshNormalMaterial();
const cube = new THREE.Mesh(
    geometry,
    material
);

scene.add(cube);

// ------------------------------------------------------------
// Load Python
// ------------------------------------------------------------

status.textContent = "Loading Python...";
const pyodide = await loadPyodide();

// ------------------------------------------------------------
// Load our Python game
// ------------------------------------------------------------

status.textContent = "Starting game...";

const pythonSource = `
import sys
sys.path.insert(0, "/game")
from game import Game
game = Game()
`;

pyodide.FS.mkdir("/game");


// Copy our Python files into Pyodide's virtual filesystem.
const pythonFiles = [
    "game/__init__.py",
    "game/game.py",
    "game/state.py",
    "game/world.py",
    "game/player.py",
    "game/physics.py"
];

for (const file of pythonFiles) {

    const response = await fetch(file);

    if (!response.ok) {
        throw new Error(`Failed to load ${file}`);
    }

    const text = await response.text();

    const path = "/game/" + file;

    const directory =
        path.substring(0, path.lastIndexOf("/"));

    try {
        pyodide.FS.mkdirTree(directory);
    } catch {
        // Directory already exists.
    }

    pyodide.FS.writeFile(path, text);
}

pyodide.runPython(pythonSource);


// Get the Python Game object.
const game = pyodide.globals.get("game");
status.textContent = "Running";

// ------------------------------------------------------------
// Game loop
// ------------------------------------------------------------
let previousTime = performance.now();

function frame(time) {
    const dt = Math.min((time - previousTime) / 1000, 0.1);
    previousTime = time;

    // Run the Python simulation.
    game.update(dt);


    // Get Python render state.
    const objects = game.render_state().toJs();

    const player = objects[0];
    const transform = player.transform;
    const position = transform.position;
    const rotation = transform.rotation;

    // Apply Python state to Three.js object.
    cube.position.set(
        position[0],
        position[1],
        position[2]
    );

    cube.rotation.set(
        rotation[0],
        rotation[1],
        rotation[2]
    );


    // Render.
    renderer.render(scene, camera);
    requestAnimationFrame(frame);
}

requestAnimationFrame(frame);


// ------------------------------------------------------------
// Resize
// ------------------------------------------------------------

window.addEventListener("resize", () => {

    camera.aspect =
        window.innerWidth / window.innerHeight;

    camera.updateProjectionMatrix();

    renderer.setSize(
        window.innerWidth,
        window.innerHeight
    );
});