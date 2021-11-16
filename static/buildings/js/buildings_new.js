const copy = '© <a href="https://osm.org/copyright">OpenStreetMap</a> contributors'
const url = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
const osm = L.tileLayer(url, { attribution: copy })
const map = L.map('mapid', { layers: [osm] })

const buildMarker = L.divIcon({
  html: '<i class="fa fa-building fa-2x" style="color: blue;"></i>',
  iconSize: [20, 20], iconAnchor: [10, 20], popupAnchor: [0, -18],
  className: 'build-marker'
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

async function render_buildings() {
  let buildgeo = await load_buildings();
  markers = L.geoJSON(buildgeo,
    { pointToLayer: buildingPointToLayer, onEachFeature: onEachBuildingFeature, icon: buildMarker })
  markers.addTo(map)
  map.fitBounds(markers.getBounds());
  return;
}

render_buildings();
