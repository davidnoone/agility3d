

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


// ------------------------------------------------------------
// Three.js scene and camera
// ------------------------------------------------------------

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x202020);

const camera = new THREE.PerspectiveCamera(
    60,
    window.innerWidth / window.innerHeight,
    0.1,
    100
);

camera.position.set(0, 0, 5);


// ------------------------------------------------------------
// Renderer-side object collection
// ------------------------------------------------------------

const renderObjects = new Map();


// ------------------------------------------------------------
// Geometry/material definitions
// ------------------------------------------------------------

const geometries = {
    cube: new THREE.BoxGeometry(2, 2, 2)
};

const materials = {
    cube: new THREE.MeshNormalMaterial()
};


// ------------------------------------------------------------
// Create a Three.js object for a Python render object
// ------------------------------------------------------------

function createRenderObject(geometryName) {
    const geometry = geometries[geometryName];
    const material = materials[geometryName];

    if (!geometry || !material) {
        throw new Error(
            `Unknown geometry: ${geometryName}`
        );
    }

    return new THREE.Mesh(geometry, material);
}


// ------------------------------------------------------------
// Synchronize Three.js objects with Python world objects
// ------------------------------------------------------------

function updateRenderObjects(objects) {
    const activeIds = new Set();

    for (const object of objects) {
        const id       = object[0];
        const geometry = object[1];

        const px = object[2];
        const py = object[3];
        const pz = object[4];

        const rx = object[5];
        const ry = object[6];
        const rz = object[7];

        activeIds.add(id);

        // Create renderer object if it does not exist yet.
        let renderObject = renderObjects.get(id);

        if (!renderObject) {
            renderObject = createRenderObject(geometry);

            renderObjects.set(id, renderObject);
            scene.add(renderObject);
        }

        // Update transform.
        renderObject.position.set(px, py, pz);
        renderObject.rotation.set(rx, ry, rz);
    }

    // Remove renderer objects which no longer exist in Python.
    for (const [id, renderObject] of renderObjects) {
        if (!activeIds.has(id)) {
            scene.remove(renderObject);
            renderObjects.delete(id);
        }
    }
}


// ------------------------------------------------------------
// Start Python / Pyodide
// ------------------------------------------------------------

status.textContent = "Loading Python...";

const pyodide = await loadPyodide();

status.textContent = "Starting game...";


// ------------------------------------------------------------
// Load Python game files into Pyodide
// ------------------------------------------------------------

pyodide.FS.mkdir("/game");

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


// ------------------------------------------------------------
// Create the Python game
// ------------------------------------------------------------

const pythonSource = `
import sys

sys.path.insert(0, "/game")

from game import Game

game = Game()
`;

pyodide.runPython(pythonSource);

const game = pyodide.globals.get("game");

status.textContent = "Running";


// ------------------------------------------------------------
// Animation loop
// ------------------------------------------------------------

let previousTime = performance.now();

function frame(time) {
    const dt = Math.min(
        (time - previousTime) / 1000,
        0.1
    );

    previousTime = time;

    // Update game simulation in Python.
    game.update(dt);

    // Obtain render state from Python.
    const objects = game.render_state().toJs();

    // Synchronize Three.js scene with Python world.
    updateRenderObjects(objects);

    // Render.
    renderer.render(scene, camera);

    requestAnimationFrame(frame);
}

requestAnimationFrame(frame);


// ------------------------------------------------------------
// Handle window resizing
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
