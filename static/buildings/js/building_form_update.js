const map_data = JSON.parse(document.getElementById("map_data").textContent);

var mymap = L.map('mapid').setView([map_data.build.lat, map_data.build.long], map_data.build.zoom);

L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}', {
  attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
  maxZoom: 23,
  id: 'mapbox/streets-v11',
  tileSize: 512,
  zoomOffset: -1,
  accessToken: map_data.mapbox_token
}).addTo(mymap);

const buildMarker = L.divIcon({
  html: '<i class="fa fa-building fa-2x" style="color: blue;"></i>',
  iconSize: [20, 20], iconAnchor: [10, 20], popupAnchor: [0, -18],
  className: 'build-marker'
});

var content = "<h5>" + map_data.build.title + "</h5><img src=\"" +
  map_data.build.fb_path + "\">";
L.marker([ map_data.build.lat , map_data.build.long ], {icon: buildMarker})
  .bindPopup(content, {minWidth: 300}).addTo(mymap);

function onMapClick(e) {
  var inputlat = document.getElementById("id_lat");
  var inputlong = document.getElementById("id_long");
  var inputzoom = document.getElementById("id_zoom");
  inputlat.setAttribute('value', e.latlng.lat);
  inputlong.setAttribute('value', e.latlng.lng);
  inputzoom.setAttribute('value', mymap.getZoom());
}

mymap.on('click', onMapClick);
