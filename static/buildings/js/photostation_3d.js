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

async function load_camera_data(stat_id) {
	let response = await fetch(`/build-api/station/` + stat_id + `/camera/`);
	let cam_data = await response.json();
	return cam_data;
}

async function load_all_geometries(stat_id) {
	let response = await fetch(`/build-api/station/` + stat_id + `/dxf/`);
	let all_geom = await response.json();
	return all_geom;
}

async function workflow() {
	let cam_data = await load_camera_data(map_data.stat_id)
	let geom_data = await load_all_geometries(map_data.stat_id)
	init(cam_data, geom_data);
	animate();
}

workflow();

function init(cam_data, geom_data) {
	//camera plane

	const elev = (cam_data.camera_position.z-1.6)*6.25;

	camera = new THREE.PerspectiveCamera( 75, window.innerWidth / window.innerHeight, 1, 1000 );
	//scale eye height to 10
	camera.position.y = cam_data.camera_position.z*6.25-elev;

	scene = new THREE.Scene();
	scene.background = new THREE.Color( 0xffffff );
	scene.fog = new THREE.Fog( 0xffffff, 0, 750 );

	const light = new THREE.HemisphereLight( 0xeeeeff, 0x777788, 0.75 );
	light.position.set( 0.5, 1-elev, 0.75 );
	scene.add( light );
	const dirLight = new THREE.DirectionalLight( 0xffffff, 0.5 );
	dirLight.position.set( -50, 100-elev, 50 );
	dirLight.target.position.set( 0, 0-elev, 0 )
	dirLight.castShadow = true;
	dirLight.shadow.camera.left = -100;
	dirLight.shadow.camera.right = 100;
	dirLight.shadow.camera.bottom = -100;
	dirLight.shadow.camera.top = 100;
	dirLight.shadow.mapSize.width = 512*4; // default
	dirLight.shadow.mapSize.height = 512*4; // default
	dirLight.shadow.camera.near = 0.5; // default
	dirLight.shadow.camera.far = 500; // default
	scene.add( dirLight );
	scene.add( dirLight.target );
	//const cameraHelper = new THREE.CameraHelper(dirLight.shadow.camera);
	//scene.add(cameraHelper);

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
	const material = new THREE.MeshStandardMaterial( {color: 0xcccccc, side: THREE.DoubleSide} );
	const floor = new THREE.Mesh( geometry, material );
	floor.position.set( 0, cam_data.floor-.01-elev, 0 )
	floor.receiveShadow = true;
	scene.add( floor );

	let position = geometry.attributes.position;

	// objects

	let gm;
	let slat = cam_data.camera_position.lat
	let slong = cam_data.camera_position.long
	let arc = 6315*1000*Math.PI/180
	let correct = Math.abs(Math.cos(slat*Math.PI/180))
	let normalz = new THREE.Vector3(0,0,1)
	for (gm of geom_data){
		if (gm.geomjson == null) { continue; }
		let olat = gm.geomjson.geodata.lat
		let olong = gm.geomjson.geodata.long
		let deltay = (slat-olat)*arc
		let deltax = (slong-olong)*arc*correct
		switch ( gm.geomjson.type ){
			case 'polygon':
				let contour = [];
				let normal = new THREE.Vector3(gm.geomjson.normal[0],
					gm.geomjson.normal[1],gm.geomjson.normal[2])
				let quaternion = new THREE.Quaternion().setFromUnitVectors(normal, normalz);
				let quaternionBack = new THREE.Quaternion().setFromUnitVectors(normalz, normal);
				let i;
				for( i of gm.geomjson.vert ){
					if (normal['z']==1) {
						contour.push( new THREE.Vector3( i[0], i[1], i[2] ) );
					} else {
						contour.push( new THREE.Vector3( i[0]-gm.geomjson.vert[0][0],
							i[1]- gm.geomjson.vert[0][1],
							i[2]-gm.geomjson.vert[0][2] ).applyQuaternion(quaternion) );
					}
				}
				let objshape = new THREE.Shape( contour );
				let objgeometry, material;
				if (gm.thickness){
					let extrudeSettings = { depth: gm.thickness, bevelEnabled: false };
					objgeometry = new THREE.ExtrudeGeometry( objshape, extrudeSettings );
					material = new THREE.MeshStandardMaterial( {
						color: gm.color_field
					 } );
				} else {
					objgeometry = new THREE.ShapeGeometry( objshape )
					material = new THREE.MeshStandardMaterial( {
						color: gm.color_field,
						side: THREE.DoubleSide
					 } );
				}
				let mesh = new THREE.Mesh( objgeometry, material );
				if (normal['z'] !=1) {
					mesh.applyQuaternion(quaternionBack)
					mesh.position.set(gm.geomjson.vert[0])
				}
				mesh.rotateX( - Math.PI / 2 );
				mesh.scale.set(6.25,6.25,6.25)
				mesh.position.set(deltax*6.25, -elev, -deltay*6.25)
				mesh.receiveShadow = true;
				mesh.castShadow = true;
				scene.add(mesh)
				break;
			case 'polyline':
				let points = [];
				let p;
				for( p of gm.geomjson.vert ){
					points.push( new THREE.Vector3( p[0],  p[1], p[2] ) );
				}
				let geometry = new THREE.BufferGeometry().setFromPoints( points );
				let pmaterial = new THREE.LineBasicMaterial( {
					color: gm.color_field,
				 } );
				let line = new THREE.Line( geometry, pmaterial );
				line.rotateX( - Math.PI / 2 );
				line.scale.set(6.25,6.25,6.25)
				line.position.set(deltax*6.25, -elev, -deltay*6.25)
				scene.add(line)
				break;
			case 'line':
			let lpoints = [];
			let l;
				for( l of gm.geomjson.vert ){
					lpoints.push( new THREE.Vector3( l[0],  l[1], l[2] ) );
				}
				let lgeometry = new THREE.BufferGeometry().setFromPoints( lpoints );
				let lmaterial = new THREE.LineBasicMaterial( {
					color: gm.color_field,
				 } );
				let lline = new THREE.Line( lgeometry, lmaterial );
				lline.rotateX( - Math.PI / 2 );
				lline.scale.set(6.25,6.25,6.25)
				lline.position.set(deltax*6.25, -elev, -deltay*6.25)
				scene.add(lline)
				break;
		}
	}

	//

	renderer = new THREE.WebGLRenderer( { antialias: true } );
	renderer.setPixelRatio( window.devicePixelRatio );
	renderer.setSize( window.innerWidth, window.innerHeight );
	renderer.shadowMap.enabled = true;
	renderer.shadowMap.type = THREE.PCFSoftShadowMap;
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
