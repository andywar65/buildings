const map_data = JSON.parse(document.getElementById("map_data").textContent);

var base_map = L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}', {
  attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
  maxZoom: 23,
  id: 'mapbox/streets-v11',
  tileSize: 512,
  zoomOffset: -1,
  accessToken: map_data.mapbox_token
});

if (map_data.plans){
  for (plan of map_data.plans){
    window['plan_' + plan.id ] = L.layerGroup();
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
      object.addTo(window['plan_' + plan.id ]);
    }
  }
}

var layers = [ base_map, ];
if ( map_data.plans ){
  for ( plan of map_data.plans ){
    if ( plan.visible ){
      layers.push( window[ 'plan_' + plan.id ]);
    }
  }
}

var mymap = L.map('mapid', {
  center: [ map_data.build.lat , map_data.build.long ],
  zoom: map_data.build.zoom ,
  layers: layers
});

const buildMarker = L.divIcon({
  html: '<i class="fa fa-building fa-2x" style="color: blue;"></i>',
  iconSize: [20, 20], iconAnchor: [10, 20], popupAnchor: [0, -18],
  className: 'build-marker'
});

var content = "<h5><a href=\"" + map_data.build.path + "\">" +
  map_data.build.title +
  "</a></h5><img src=\"" + map_data.build.fb_path + "\"><br><small>" +
    map_data.build.intro + "</small>"
L.marker([ map_data.build.lat , map_data.build.long ], {icon: buildMarker})
  .addTo(mymap).bindPopup(content, {minWidth: 300});

if (map_data.hasOwnProperty('stat')){
  const statMarker = L.divIcon({
    html: '<i class="fa fa-camera fa-2x" style="color: red;"></i>',
    iconSize: [20, 20], iconAnchor: [10, 20], popupAnchor: [0, -18],
    className: 'stat-marker'
  });

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


var baseMaps = {
  "Base": base_map
};

var overlayMaps = {};
if ( map_data.plans ){
  for ( plan of map_data.plans ){
    overlayMaps[ plan.title ] = window[ 'plan_' + plan.id ];
  }
}

L.control.layers(baseMaps, overlayMaps).addTo(mymap);

function onMapClick(e) {
  var inputlat = document.getElementById("id_lat");
  var inputlong = document.getElementById("id_long");
  inputlat.setAttribute('value', e.latlng.lat);
  inputlong.setAttribute('value', e.latlng.lng);
}

mymap.on('click', onMapClick);
