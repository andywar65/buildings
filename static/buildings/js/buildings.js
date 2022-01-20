const map_data = JSON.parse(document.getElementById("map_data").textContent);

const copy = '© <a href="https://osm.org/copyright">OpenStreetMap</a> contributors'
const url = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'

var base_map = L.tileLayer(url, {
  attribution: copy,
  maxZoom: 23,
});

var sat_map = L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}', {
  attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
  maxZoom: 23,
  tileSize: 512,
  zoomOffset: -1,
  id: 'mapbox/satellite-v9',
  accessToken: map_data.mapbox_token
});

const buildMarker = L.AwesomeMarkers.icon({
    icon: 'fa-building',
    prefix: 'fa',
    markerColor: 'blue',
    iconColor: 'white',
  });

const statMarker = L.AwesomeMarkers.icon({
    icon: 'fa-camera',
    prefix: 'fa',
    markerColor: 'red',
    iconColor: 'white',
  });

const elemMarker = L.AwesomeMarkers.icon({
    icon: 'fa-thumb-tack',
    prefix: 'fa',
    markerColor: 'green',
    iconColor: 'white',
  });

const locationMarker = L.AwesomeMarkers.icon({
    icon: 'fa-street-view',
    prefix: 'fa',
    markerColor: 'orange',
    iconColor: 'black',
  });

async function load_dxf(plan_id) {
  let response = await fetch(`/build-api/dxf/by-plan/` + plan_id);
  let geojson = await response.json();
  return geojson;
}

function setDxfStyle(feature) {
  switch ( feature.geometry.type ){
    case 'LineString':
      return {
        color: feature.properties.color_field,
      };
      break;
    case 'Polygon':
      return {
        fillColor: feature.properties.color_field,
        color: feature.properties.color_field,
        fillOpacity: 0.5,
      };
      break;
  }
}

function onEachDxfFeature(feature, layer) {
  layer.bindPopup( feature.properties.layer );//+ feature.properties.data
}

async function render_dxf(plan_id, layergroup) {
  let dxfgeo = await load_dxf(plan_id);
  L.geoJSON(dxfgeo, { style :setDxfStyle, onEachFeature: onEachDxfFeature }
    ).addTo(layergroup)
  return;
}

if (map_data.hasOwnProperty('plans')){
  for (plan of map_data.plans){
    window['plan_' + plan.id ] = L.layerGroup();
    if (plan.geometry){
      for (obj of plan.geometry){
        switch ( obj.type ){
          case 'polygon':
            var object = L.polygon( obj.coords, {color: obj.color,
              fillcolor: obj.color, fillOpacity: 0.5});
            break;
          case 'polyline':
            var object = L.polyline( obj.coords, {color: obj.color});
            break;
          case 'circle':
            var object = L.circle( obj.coords, {radius: obj.radius,
              color: obj.color, fillcolor: obj.color, fillOpacity: 0.5});
            break;
        }
        if (map_data.hasOwnProperty('no_plan_popup')){
          object.addTo(window['plan_' + plan.id ]);
        } else {
          object.bindPopup(obj.popup).addTo(window['plan_' + plan.id ]);
        }
      }
    }
    render_dxf(plan.id, window['plan_' + plan.id ]);
  }
}

if (map_data.hasOwnProperty('no_plan_status')){
  if (map_data.no_plan_status){
    var no_plan = L.layerGroup();
  }
}

if (map_data.hasOwnProperty('stations')){
  if (map_data.stations){
    for (stat of map_data.stations){
      if (stat.fb_path){
        var content = "<h5><a href=\"" + stat.path + "\">" + stat.title +
          "</a></h5><img src=\"" + stat.fb_path + "\"><br><small>" +
            stat.intro + "</small>";
      } else {
        var content = "<h5><a href=\"" + stat.path + "\">" + stat.title +
          "</a></h5><br><small>" + stat.intro + "</small>";
      }
      var marker = L.marker([stat.lat, stat.long ], {icon: statMarker})
        .bindPopup( content, {minWidth: 300});
      if (stat.plan_id){
        marker.addTo(window['plan_' + stat.plan_id ]);
      } else {
        marker.addTo( no_plan );
      }
    }
  }
}

if (map_data.hasOwnProperty('elements')){
  if (map_data.elements){
    for (elem of map_data.elements){
      var sheet = ""
      for (const [key, value] of Object.entries(elem.sheet)) {
        sheet = sheet + "<li>" + key + " - " + value + "</li>"
      }
      if (elem.fb_path){
        var content = "<h5><a href=\"" + elem.path + "\">" + elem.title +
          "</a></h5><img src=\"" + elem.fb_path + "\"><br><small>" +
            elem.intro + "<ul>" + sheet + "</ul></small>";
      } else {
        var content = "<h5><a href=\"" + elem.path + "\">" + elem.title +
          "</a></h5><br><small>" + elem.intro +
          "<ul>" + sheet + "</ul></small>";
      }
      var marker = L.marker([elem.lat, elem.long ], {icon: elemMarker})
        .bindPopup( content, {minWidth: 300});
      if (elem.plan_id){
        marker.addTo(window['plan_' + elem.plan_id ]);
      } else {
        marker.addTo( no_plan );
      }
    }
  }
}

var layers = [ base_map, ];

if (map_data.hasOwnProperty('plans')){
  for ( plan of map_data.plans ){
    if ( plan.visible ){
      layers.push( window[ 'plan_' + plan.id ]);
    }
  }
}
if (map_data.hasOwnProperty('no_plan_status')){
  if (map_data.no_plan_status){
    layers.push( no_plan )
  }
}

if (map_data.hasOwnProperty('city_lat')){
  var mymap = L.map('mapid', {
    center: [ map_data.city_lat , map_data.city_long ],
    zoom: map_data.city_zoom,
    layers: layers
  });
} else {
  var mymap = L.map('mapid', {
    center: [ map_data.build.lat , map_data.build.long ],
    zoom: map_data.build.zoom,
    layers: layers
  });
}

const locationGroup = L.layerGroup().addTo(mymap);

if (map_data.hasOwnProperty('builds')){
  for (build of map_data.builds ){
    var content = "<h5><a href=\"" + build.path + "\">" + build.title
      "</a></h5><img src=\"" + build.fb_path + "\"><br><small>" +
        build.intro + "</small>"
    L.marker([ build.lat , build.long ], {icon: buildMarker}).addTo(mymap)
      .bindPopup(content, {minWidth: 300});
  }
}

if (map_data.hasOwnProperty('build')){
  var content = "<h5>" + map_data.build.title + "</h5><img src=\"" +
    map_data.build.fb_path + "\">";
  L.marker([ map_data.build.lat , map_data.build.long ], {icon: buildMarker})
    .bindPopup(content, {minWidth: 300}).addTo(mymap);
}

if (map_data.hasOwnProperty('stat')){
  if (map_data.stat.fb_path){
    var content = "<h5>" + map_data.stat.title +
      "</h5><img src=\"" + map_data.stat.fb_path + "\"><br><small>" +
        map_data.stat.intro + "</small>";
  } else {
    var content = "<h5>" + map_data.stat.title +
      "</h5><br><small>" + map_data.stat.intro + "</small>";
  }
  L.marker([map_data.stat.lat, map_data.stat.long ], {icon: statMarker})
    .addTo(mymap).bindPopup( content, {minWidth: 300});
}

if (map_data.hasOwnProperty('elem')){
  if (map_data.elem.fb_path){
    var content = "<h5>" + map_data.elem.title +
      "</h5><img src=\"" + map_data.elem.fb_path + "\"><br><small>" +
        map_data.elem.intro + "</small>";
  } else {
    var content = "<h5>" + map_data.elem.title +
      "</h5><br><small>" + map_data.elem.intro + "</small>";
  }
  L.marker([map_data.elem.lat, map_data.elem.long ], {icon: elemMarker})
    .addTo(mymap).bindPopup( content, {minWidth: 300});
}

var baseMaps = {
  "Base": base_map,
  "Satellite": sat_map
};

var overlayMaps = {};
if (map_data.hasOwnProperty('plans')){
  for ( plan of map_data.plans ){
    overlayMaps[ plan.title ] = window[ 'plan_' + plan.id ];
  }
}
if (map_data.hasOwnProperty('no_plan_status')){
  if (map_data.no_plan_status){
    overlayMaps[ map_data.no_plan_trans ] = no_plan;
  }
}

L.control.layers(baseMaps, overlayMaps).addTo(mymap);

if (map_data.hasOwnProperty('on_map_click')){
  function onMapClick(e) {
    var inputlat = document.getElementById("id_lat");
    var inputlong = document.getElementById("id_long");
    inputlat.setAttribute('value', e.latlng.lat);
    inputlong.setAttribute('value', e.latlng.lng);
    if (map_data.hasOwnProperty('on_map_zoom')){
      var inputzoom = document.getElementById("id_zoom");
      inputzoom.setAttribute('value', mymap.getZoom());
    }
  }

  mymap.on('click', onMapClick);
}

function userFound(e) {
  let content = "You are here (accuracy " + e.accuracy + " meters)!";
  L.marker( e.latlng , {icon: locationMarker}).bindPopup(content).addTo(locationGroup);
  L.circle(e.latlng, e.accuracy).addTo(locationGroup);
  mymap.fitBounds([e.latlng, [map_data.build.lat , map_data.build.long]],
    {padding: [50,50]});
}

function userNotFound(e) {
    alert(e.message);
}

function locateUser() {
  locationGroup.clearLayers();
  mymap.locate().on('locationfound', userFound).on('locationerror', userNotFound);
}
