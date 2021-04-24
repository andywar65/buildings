import * as THREE from './three/v0.127.0/build/three.module.js';

import { PointerLockControls } from './three/v0.127.0/examples/jsm/controls/PointerLockControls.js';

const map_data = JSON.parse(document.getElementById("map_data").textContent);

let camera, scene, renderer, controls;

const objects = [];

let raycaster;

let moveForward = false;
let moveBackward = false;
let moveLeft = false;
let moveRight = false;
let canJump = false;

let prevTime = performance.now();
const velocity = new THREE.Vector3();
const direction = new THREE.Vector3();
const vertex = new THREE.Vector3();
const color = new THREE.Color();

init();
animate();

function init() {

	camera = new THREE.PerspectiveCamera( 75, window.innerWidth / window.innerHeight, 1, 1000 );
	//scale eye height to 10
	camera.position.x = map_data.camera[0]*6.25;
	camera.position.y = map_data.camera[1]*6.25;
	camera.position.z = map_data.camera[2]*6.25;

	scene = new THREE.Scene();
	scene.background = new THREE.Color( 0xffffff );
	scene.fog = new THREE.Fog( 0xffffff, 0, 750 );

	const light = new THREE.HemisphereLight( 0xeeeeff, 0x777788, 0.75 );
	light.position.set( 0.5, 1, 0.75 );
	scene.add( light );

	controls = new PointerLockControls( camera, document.body );

	const blocker = document.getElementById( 'blocker' );
	const instructions = document.getElementById( 'instructions' );

	instructions.addEventListener( 'click', function () {

		controls.lock();

	} );

	controls.addEventListener( 'lock', function () {

		instructions.style.display = 'none';
		blocker.style.display = 'none';

	} );

	controls.addEventListener( 'unlock', function () {

		blocker.style.display = 'block';
		instructions.style.display = '';

	} );

	scene.add( controls.getObject() );

	const onKeyDown = function ( event ) {

		switch ( event.code ) {

			case 'ArrowUp':
			case 'KeyW':
				moveForward = true;
				break;

			case 'ArrowLeft':
			case 'KeyA':
				moveLeft = true;
				break;

			case 'ArrowDown':
			case 'KeyS':
				moveBackward = true;
				break;

			case 'ArrowRight':
			case 'KeyD':
				moveRight = true;
				break;

			case 'Space':
				if ( canJump === true ) velocity.y += 350;
				canJump = false;
				break;

		}

	};

	const onKeyUp = function ( event ) {

		switch ( event.code ) {

			case 'ArrowUp':
			case 'KeyW':
				moveForward = false;
				break;

			case 'ArrowLeft':
			case 'KeyA':
				moveLeft = false;
				break;

			case 'ArrowDown':
			case 'KeyS':
				moveBackward = false;
				break;

			case 'ArrowRight':
			case 'KeyD':
				moveRight = false;
				break;

		}

	};

	document.addEventListener( 'keydown', onKeyDown );
	document.addEventListener( 'keyup', onKeyUp );

	raycaster = new THREE.Raycaster( new THREE.Vector3(), new THREE.Vector3( 0, - 1, 0 ), 0, 10 );

	// floor

	const geometry = new THREE.PlaneGeometry( 2000, 2000, 32 );
	geometry.rotateX( - Math.PI / 2 );
	const material = new THREE.MeshBasicMaterial( {color: 0xcccccc, side: THREE.DoubleSide} );
	const floor = new THREE.Mesh( geometry, material );
	floor.position.set( 0, -.01, 0 )
	scene.add( floor );

	let position = geometry.attributes.position;

	// objects
	let gm;
	for (gm of map_data.geom){
		switch ( gm.type ){
			case 'polygon':
				let contour = [];
				let i;
				for( i of gm.coords ){
					contour.push( new THREE.Vector2( i[0],  i[1] ) );
				}
				let objshape = new THREE.Shape( contour );
				let objgeometry, material;
				if (gm.depth){
					let extrudeSettings = { amount: gm.depth, bevelEnabled: false };
					objgeometry = new THREE.ExtrudeGeometry( objshape, extrudeSettings );
					material = new THREE.MeshBasicMaterial( {
						color: gm.color
					 } );
				} else {
					objgeometry = new THREE.ShapeGeometry( objshape )
					material = new THREE.MeshBasicMaterial( {
						color: gm.color,
						side: THREE.DoubleSide
					 } );
				}
				let mesh = new THREE.Mesh( objgeometry, material );
				mesh.rotateX( - Math.PI / 2 );
				let pos = gm.position
				mesh.position.set( pos[0], pos[1], pos[2], );
				mesh.rotateZ( gm.rotation[2] );
				mesh.rotateX( gm.rotation[0] );
				mesh.rotateY( gm.rotation[1] );
				scene.add(mesh)
				break;
			case 'polyline':
				let points = [];
				let p;
				for( p of gm.coords ){
					points.push( new THREE.Vector2( p[0],  p[1] ) );
				}
				let geometry = new THREE.BufferGeometry().setFromPoints( points );
				let pmaterial = new THREE.LineBasicMaterial( {
					color: gm.color,
				 } );
				let line = new THREE.Line( geometry, pmaterial );
				line.rotateX( - Math.PI / 2 );
				let ppos = gm.position
				line.position.set( ppos[0], ppos[1], ppos[2], );
				line.rotateZ( gm.rotation[2] );
				line.rotateX( gm.rotation[0] );
				line.rotateY( gm.rotation[1] );
				scene.add(line)
				break;
			case 'line':
			let lpoints = [];
			let l;
				for( l of gm.coords ){
					lpoints.push( new THREE.Vector3( l[0],  l[2],  l[1] ) );
				}
				let lgeometry = new THREE.BufferGeometry().setFromPoints( lpoints );
				let lmaterial = new THREE.LineBasicMaterial( {
					color: gm.color,
				 } );
				let lline = new THREE.Line( lgeometry, lmaterial );
				scene.add(lline)
				break;
		}
	}

	//

	renderer = new THREE.WebGLRenderer( { antialias: true } );
	renderer.setPixelRatio( window.devicePixelRatio );
	renderer.setSize( window.innerWidth, window.innerHeight );
	document.body.appendChild( renderer.domElement );

	//

	window.addEventListener( 'resize', onWindowResize );

}

function onWindowResize() {

	camera.aspect = window.innerWidth / window.innerHeight;
	camera.updateProjectionMatrix();

	renderer.setSize( window.innerWidth, window.innerHeight );

}

function animate() {

	requestAnimationFrame( animate );

	const time = performance.now();

	if ( controls.isLocked === true ) {

		raycaster.ray.origin.copy( controls.getObject().position );
		raycaster.ray.origin.y -= 10;

		const intersections = raycaster.intersectObjects( objects );

		const onObject = intersections.length > 0;

		const delta = ( time - prevTime ) / 1000;

		velocity.x -= velocity.x * 10.0 * delta;
		velocity.z -= velocity.z * 10.0 * delta;

		velocity.y -= 9.8 * 100.0 * delta; // 100.0 = mass

		direction.z = Number( moveForward ) - Number( moveBackward );
		direction.x = Number( moveRight ) - Number( moveLeft );
		direction.normalize(); // this ensures consistent movements in all directions

		if ( moveForward || moveBackward ) velocity.z -= direction.z * 400.0 * delta;
		if ( moveLeft || moveRight ) velocity.x -= direction.x * 400.0 * delta;

		if ( onObject === true ) {

			velocity.y = Math.max( 0, velocity.y );
			canJump = true;

		}

		controls.moveRight( - velocity.x * delta );
		controls.moveForward( - velocity.z * delta );

		controls.getObject().position.y += ( velocity.y * delta ); // new behavior

		if ( controls.getObject().position.y < 10 ) {

			velocity.y = 0;
			controls.getObject().position.y = 10;

			canJump = true;

		}

	}

	prevTime = time;

	renderer.render( scene, camera );

}
