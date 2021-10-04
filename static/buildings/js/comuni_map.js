const copy = '© <a href="https://osm.org/copyright">OpenStreetMap</a> contributors'
const url = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
const osm = L.tileLayer(url, { attribution: copy })
const map = L.map('map', {
  center: [ 41.8988 , 12.5451 ],
  zoom: 9,
  layers: [osm] })
//map.fitWorld();
