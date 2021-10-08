const copy = '© <a href="https://osm.org/copyright">OpenStreetMap</a> contributors'
const url = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
const osm = L.tileLayer(url, { attribution: copy })
const map = L.map('map', { layers: [osm] })
const layerGroup = L.layerGroup().addTo(map)
map.setView([41.8988, 12.5451], 9)

async function load_comuni() {
  let comuni_url = ``
  const zoom = map.getZoom()
  if (zoom<10){
    comuni_url = `/edifici/comuni/api/lo/?in_bbox=${map.getBounds().toBBoxString()}`
  } else {
    comuni_url = `/edifici/comuni/api/hi/?in_bbox=${map.getBounds().toBBoxString()}`
  }
  const response = await fetch(comuni_url)
  const geojson = await response.json()
  return geojson
}
async function render_comuni() {
  const comuni = await load_comuni()
  layerGroup.clearLayers()
  L.geoJSON(comuni).bindPopup(layer => layer.feature.properties.comune_com).addTo(layerGroup)
}
map.on('moveend', render_comuni)
