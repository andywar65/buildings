const map_data = JSON.parse(document.getElementById("map_data").textContent);

var mymap = L.map('mapid').setView([map_data.city_lat, map_data.city_long], map_data.city_zoom);

L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}', {
  attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
  maxZoom: 19,
  id: 'mapbox/streets-v11',
  tileSize: 512,
  zoomOffset: -1,
  accessToken: map_data.mapbox_token
}).addTo(mymap);

if ( map_data.builds ){
  const buildMarker = L.divIcon({
    html: '<i class="fa fa-building fa-2x" style="color: blue;"></i>',
    iconSize: [20, 20], iconAnchor: [10, 20], popupAnchor: [0, -18],
    className: 'build-marker'
  });
  for (build of map_data.builds ){
    var content = "<h5><a href=\"" + build.path + "\">" + build.title +
      "</a></h5><img src=\"" + build.fb_path + "\"><br><small>" +
        build.intro + "</small>"
    L.marker([ build.lat , build.long ], {icon: buildMarker}).addTo(mymap)
      .bindPopup(content, {minWidth: 300});
  }
}

function onMapClick(e) {
  var inputlat = document.getElementById("id_lat");
  var inputlong = document.getElementById("id_long");
  var inputzoom = document.getElementById("id_zoom");
  inputlat.setAttribute('value', e.latlng.lat);
  inputlong.setAttribute('value', e.latlng.lng);
  inputzoom.setAttribute('value', mymap.getZoom());
}

mymap.on('click', onMapClick);
