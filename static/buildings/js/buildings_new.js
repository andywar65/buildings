axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN"

let app = new Vue({
  delimiters: ["[[", "]]"],
  el: '#vue-app',
  data : {
      map_data : JSON.parse(document.getElementById("map_data").textContent),
      map : Object,
      buildMarker : Object,
      copy : '© <a href="https://osm.org/copyright">OpenStreetMap</a> contributors',
      url : 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      mb_copy : 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
      mb_url : 'https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}',
      mb_id : 'mapbox/satellite-v9',
      isBuildList : true,
      isCityChange : false,
      isBuildAdd : false,
      title : "",
      lat : null,
      long : null,
      zoom : null,
      image : "",
      intro : ""
    },
  methods: {
    setupLeafletMap: function () {

      const base_map = L.tileLayer(this.url, {
        attribution: this.copy,
        maxZoom: 23,
      }).addTo(this.map)

      const sat_map = L.tileLayer(this.mb_url, {
        attribution: this.mb_copy,
        maxZoom: 23,
        tileSize: 512,
        zoomOffset: -1,
        id: this.mb_id,
        accessToken: this.map_data.mapbox_token
      })

      //const map = L.map('mapid', { layers: [base_map] })

      const baseMaps = {
        "Base": base_map,
        "Satellite": sat_map
      }

      L.control.layers(baseMaps, ).addTo(this.map)

      this.map.on('click', this.onMapClick)

      this.map.on('zoomend', this.onMapZoomEnd)

    },
    load_buildings : async function () {
      let response = await fetch(`/build-api/all/`)
      let geojson = await response.json()
      return geojson
    },
    buildingPointToLayer : function (feature, latlng) {
      return L.marker(latlng, {icon: this.buildMarker})
    },
    onEachBuildingFeature : function (feature, layer) {
      let content = "<h5><a href=\"" + feature.properties.path + "\">" +
        feature.properties.title +
        "</a></h5><img src=\"" + feature.properties.image_path + "\"><br><small>" +
        feature.properties.intro + "</small>"
      layer.bindPopup(content, {minWidth: 300})
    },
    setCityView : async function () {
      let response = await fetch(`/build-api/city/`)
      let cityjson = await response.json()
      try {
        city = cityjson.features[0]
        this.map.setView([city.geometry.coordinates[1], city.geometry.coordinates[0]],
          city.properties.zoom)
      } catch {
        this.map.setView([41.8988, 12.5451], 10)
      }
    },
    render_buildings : async function () {
      let buildgeo = await this.load_buildings()
      markers = L.geoJSON(buildgeo,
        { pointToLayer: this.buildingPointToLayer, onEachFeature: this.onEachBuildingFeature })
      markers.addTo(this.map)
      try {
        this.map.fitBounds(markers.getBounds(), {padding: [50,50]})
      }
      catch {
        this.map.locate()
          .on('locationfound', e => this.map.setView(e.latlng, 10))
          .on('locationerror', () => this.setCityView())
      }
    },
    onCityPanel : function () {
      this.isBuildList = false
      this.isCityChange = true
    },
    onBuildPanel : function () {
      this.isBuildList = false
      this.isBuildAdd = true
    },
    onCityDismiss : function () {
      this.isBuildList = true
      this.isCityChange = false
    },
    onBuildDismiss : function () {
      this.isBuildList = true
      this.isBuildAdd = false
    },
    onMapClick : function (e) {
      this.lat = e.latlng.lat
      this.long = e.latlng.lng
    },
    onMapZoomEnd : function () {
      this.zoom = this.map.getZoom()
    },
    clearData : function () {
      this.title = ""
      this.lat = null
      this.long = null
      this.zoom = null
      this.image = ""
      this.intro = ""
    },
    onCityAdd : function () {
      let url = '/build-api/city/add/'
      let data = {
          "name": this.title,
          "lat": this.lat,
          "long": this.long,
          "zoom": this.zoom
      }
      axios
          .post(url, data)
          .then(response => {
            this.isBuildList = true
            this.isCityChange = false
            this.clearData()
          })
          .catch(error => {
              console.log(error)
          })
    },
    onBuildAdd : function () {
      let url = '/build-api/add/'
      let data = {
          "title": this.title,
          "intro": this.intro,
          "lat": this.lat,
          "long": this.long,
          "zoom": this.zoom
      }
      axios
          .post(url, data)
          .then(response => {
            this.isBuildList = true
            this.isBuildAdd = false
            this.clearData()
            this.setupLeafletMap()
          })
          .catch(error => {
              console.log(error)
          })
    },
  },
  mounted() {
    this.map = L.map('mapid')
    this.buildMarker = L.AwesomeMarkers.icon({
        icon: 'fa-building',
        prefix: 'fa',
        markerColor: 'blue',
        iconColor: 'white',
      })
    this.setupLeafletMap()
    this.render_buildings()
  }
})
