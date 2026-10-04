import { loadPyodide } from
    "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide.mjs";

import * as THREE from
    "https://cdn.jsdelivr.net/npm/three@0.180.0/build/three.module.js";

const status = document.getElementById("status");

const canvas = document.getElementById("game");

const renderer = new THREE.WebGLRenderer({
    canvas: canvas,
    antialias: true
});

renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(window.innerWidth, window.innerHeight);


const scene = new THREE.Scene();
scene.background = new THREE.Color(0x202020);

// Add lighting, else all is black
const ambientLight = new THREE.AmbientLight(0xffffff, 1.5);
scene.add(ambientLight);

const directionalLight = new THREE.DirectionalLight(0xffffff, 2);
directionalLight.position.set(1000, 2000, 3000);
scene.add(directionalLight);



// Camera, not convention for view angle vs x,y,z convention from python
const camera = new THREE.PerspectiveCamera(
    60,
    window.innerWidth / window.innerHeight,
    0.1,
    100000
);

// Position in geometry of the "world", which carries units in mm
camera.position.set(2000, 2000, 2000);
camera.up.set(0, 0, 1);     // z is "up"
camera.lookAt(0, 0, 0);


// Map from Python render ID to Three.js object.
const renderObjects = new Map();


function createRenderObject(geometryData, styleData) {

    const geometry = new THREE.BufferGeometry();

    const points = geometryData.points;
    const faces = geometryData.faces;

    // Convert vertices to a flat Float32Array.
    const positions = new Float32Array(points.length * 3);

    for (let i = 0; i < points.length; i++) {
        positions[3 * i + 0] = points[i][0];
        positions[3 * i + 1] = points[i][1];
        positions[3 * i + 2] = points[i][2];
    }

    geometry.setAttribute(
        "position",
        new THREE.BufferAttribute(positions, 3)
    );


    // Convert polygon faces to triangles.
    //
    // For now use a simple triangle fan:
    //
    // [0, 1, 2, 3] -> [0,1,2], [0,2,3]
    //
    // This is appropriate for the simple planar/convex
    // geometry currently being generated.

    const indices = [];

    for (const face of faces) {

        if (face.length < 3) {
            continue;
        }

        for (let i = 1; i < face.length - 1; i++) {
            indices.push(
                face[0],
                face[i],
                face[i + 1]
            );
        }
    }

    geometry.setIndex(indices);
    geometry.computeVertexNormals();


    console.log("style:", styleData);
    console.log("face colour:", styleData.face_color);

    const color = styleData.face_color;

    const material = new THREE.MeshStandardMaterial({
        color: new THREE.Color(
            color[0] / 255,
            color[1] / 255,
            color[2] / 255
        ),
        transparent: styleData.alpha < 1.0,
        opacity: styleData.alpha,
        side: THREE.DoubleSide
        
    });


    return new THREE.Mesh(geometry, material);
}


function updateRenderObjects(objects) {

    const activeIds = new Set();


    for (const object of objects) {

        const id = object[0];
        const geometry = object[1];
        const transform = object[2];
        const style = object[3];

        activeIds.add(id);


        let renderObject = renderObjects.get(id);


        if (!renderObject) {

            renderObject = createRenderObject(
                geometry,
                style
            );

            renderObjects.set(id, renderObject);

            scene.add(renderObject);
        }


        // The transform is a 4x4 matrix.
        //
        // Pyodide converts the numpy array into a JS array-like
        // object, so copy the values into a THREE.Matrix4.

        const matrix = new THREE.Matrix4();

        matrix.set(
            transform[0][0],
            transform[0][1],
            transform[0][2],
            transform[0][3],

            transform[1][0],
            transform[1][1],
            transform[1][2],
            transform[1][3],

            transform[2][0],
            transform[2][1],
            transform[2][2],
            transform[2][3],

            transform[3][0],
            transform[3][1],
            transform[3][2],
            transform[3][3]
        );

        renderObject.matrixAutoUpdate = false;
        renderObject.matrix.copy(matrix);
        renderObject.matrixWorldNeedsUpdate = true;


        // Visibility.

        renderObject.visible = style.visible;
    }


    // Remove objects which no longer exist in Python.

    for (const [id, renderObject] of renderObjects) {

        if (!activeIds.has(id)) {

            scene.remove(renderObject);

            renderObject.geometry.dispose();

            if (renderObject.material) {
                renderObject.material.dispose();
            }

            renderObjects.delete(id);
        }
    }
}


status.textContent = "Loading Python...";

const pyodide = await loadPyodide();
await pyodide.loadPackage("numpy")

status.textContent = "Starting game...";


pyodide.FS.mkdir("/game");


const pythonFiles = [
    "game/__init__.py",
    "game/game.py",
    "game/state.py",
    "game/world.py",
    "game/player.py",
    "game/physics.py",
    "game/classes.py",
    "game/creation.py",
    "game/primitives.py",
    "game/translations.py"
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


const pythonSource = `
import sys
sys.path.insert(0, "/game")

from game import Game

game = Game()
`;


pyodide.runPython(pythonSource);

const game = pyodide.globals.get("game");

status.textContent = "Running";


let previousTime = performance.now();


function frame(time) {
    // Update/time-step state
    const dt = Math.min( (time - previousTime) / 1000, 0.1 );
    previousTime = time;
    game.update(dt);

    // Get the objects and render them
    const objects = game.render_state().toJs();

    updateRenderObjects(objects);
    renderer.render( scene, camera);
    requestAnimationFrame(frame);
}

requestAnimationFrame(frame);


window.addEventListener("resize", () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(
        window.innerWidth,
        window.innerHeight
    );
});