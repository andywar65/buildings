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
            fillcolor: obj.color, fillOpacity: 0.5}).bindPopup(obj.popup);
          break;
        case 'polyline':
          var object = L.polyline( obj.coords, {color: obj.color})
            .bindPopup(obj.popup);
          break;
        case 'circle':
          var object = L.circle( obj.coords, {radius: obj.radius,
            color: obj.color, fillcolor: obj.color, fillOpacity: 0.5})
            .bindPopup(obj.popup);
          break;
      }
      object.addTo(window['plan_' + plan.id ]);
    }
  }
}

if (map_data.stations){
  const statMarker = L.divIcon({
    html: '<i class="fa fa-camera fa-2x" style="color: red;"></i>',
    iconSize: [20, 20], iconAnchor: [10, 20], popupAnchor: [0, -18],
    className: 'stat-marker'
  });
  if (map_data.no_plan_status){
    var no_plan = L.layerGroup();
  }
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

var layers = [ base_map, ];
if ( map_data.plans ){
  for ( plan of map_data.plans ){
    if ( plan.visible ){
      layers.push( window[ 'plan_' + plan.id ]);
    }
  }
}
if ( map_data.no_plan_status ){
  layers.push( no_plan )
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

var content = "<h5>" + map_data.build.title + "</h5><img src=\"" +
  map_data.build.fb_path + "\">";
L.marker([ map_data.build.lat , map_data.build.long ], {icon: buildMarker})
  .bindPopup(content, {minWidth: 300}).addTo(mymap);

var baseMaps = {
  "Base": base_map
};

var overlayMaps = {};
if ( map_data.plans ){
  for ( plan of map_data.plans ){
    overlayMaps[ plan.title ] = window[ 'plan_' + plan.id ];
  }
}
if ( map_data.no_plan_status ){
  overlayMaps[ map_data.no_plan_trans ] = no_plan;
}

L.control.layers(baseMaps, overlayMaps).addTo(mymap);
