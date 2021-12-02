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

const map = L.map('mapid', { layers: [base_map] })

var baseMaps = {
  "Base": base_map,
  "Satellite": sat_map
};

L.control.layers(baseMaps, ).addTo(map);

const buildMarker = L.AwesomeMarkers.icon({
    icon: 'fa-building',
    prefix: 'fa',
    markerColor: 'blue',
    iconColor: 'white',
  });

async function load_buildings() {
  let response = await fetch(`/build-api/all/`);
  let geojson = await response.json();
  return geojson;
}

function onEachBuildingFeature(feature, layer) {
  let content = "<h5><a href=\"" + feature.properties.path + "\">" +
    feature.properties.title +
    "</a></h5><img src=\"" + feature.properties.image_path + "\"><br><small>" +
    feature.properties.intro + "</small>"
  layer.bindPopup(content, {minWidth: 300});
}

function buildingPointToLayer(feature, latlng) {
  return L.marker(latlng, {icon: buildMarker});
}

async function setCityView() {
  let response = await fetch(`/build-api/city/`);
  let cityjson = await response.json();
  try {
    city = cityjson.features[0];
    map.setView([city.geometry.coordinates[1], city.geometry.coordinates[0]],
      city.properties.zoom);
  } catch {
    map.setView([41.8988, 12.5451], 10);
  }
}

async function render_buildings() {
  let buildgeo = await load_buildings();
  markers = L.geoJSON(buildgeo,
    { pointToLayer: buildingPointToLayer, onEachFeature: onEachBuildingFeature });
  markers.addTo(map);
  try {
    map.fitBounds(markers.getBounds());
  }
  catch {
    map.locate()
      .on('locationfound', e => map.setView(e.latlng, 10))
      .on('locationerror', () => setCityView());
  }
}

render_buildings();
