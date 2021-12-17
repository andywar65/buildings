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
      alert : "",
      isAlertPanel : false,
      isBuildList : true,
      isCityChange : false,
      isBuildAdd : false,
      formErrors : false,
      image : null,
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
      let response = await fetch(`/build-api/city/all/`)
      let cityjson = await response.json()
      try {
        city = cityjson.features[0]
        this.map.setView([city.geometry.coordinates[1], city.geometry.coordinates[0]],
          city.properties.zoom)
      } catch {
        this.map.setView([this.map_data.city_lat, this.map_data.city_long],
          this.map_data.city_zoom)
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
    handleImageUpload : function () {
      this.image = this.$refs.image.files[0]
    },
    onCityPanel : function () {
      this.isAlertPanel = false
      this.alert = ""
      this.isBuildList = false
      this.isCityChange = true
    },
    onBuildPanel : function () {
      this.isAlertPanel = false
      this.alert = ""
      this.isBuildList = false
      this.isBuildAdd = true
    },
    onCityDismiss : function () {
      this.isBuildList = true
      this.isCityChange = false
      this.formErrors = false
      this.clearData()
    },
    onBuildDismiss : function () {
      this.isBuildList = true
      this.isBuildAdd = false
      this.formErrors = false
      this.clearData()
    },
    onMapClick : function (e) {
      this.lat = e.latlng.lat
      this.long = e.latlng.lng
    },
    onMapZoomEnd : function () {
      this.zoom = this.map.getZoom()
    },
    clearData : function () {
      this.file = null
      this.title = ""
      this.lat = null
      this.long = null
      this.zoom = null
      this.image = ""
      this.intro = ""
      let ids = ["id_c_name", "id_c_lat", "id_c_long", "id_c_zoom", "id_b_lat",
        "id_b_long", "id_b_zoom"]
      for (id in ids) {
        let field = document.getElementById(id)
        field.setAttribute('class', "form-control")
      }
    },
    formValidation : function (value, id) {
      let field = document.getElementById(id)
      if (! value) {
        field.setAttribute('class', "form-control is-invalid")
        this.formErrors = true
      } else {
        field.setAttribute('class', "form-control is-valid")
      }
    },
    onCityAdd : function () {
      this.formErrors = false
      let url = '/build-api/city/add/'
      let data = {
          "name": this.title,
          "lat": this.lat,
          "long": this.long,
          "zoom": this.zoom
      }
      this.formValidation(this.title, "id_c_name")
      this.formValidation(this.lat, "id_c_lat")
      this.formValidation(this.long, "id_c_long")
      this.formValidation(this.zoom, "id_c_zoom")
      if (this.formErrors) { return }//prevent from sending form
      axios
          .post(url, data)
          .then(response => {
            this.isAlertPanel = true
            this.alert = this.title
            this.isBuildList = true
            this.isCityChange = false
            this.clearData()
            this.render_buildings()
          })
          .catch(error => {
              console.log(error)
          })
    },
    onBuildAdd : function () {
      this.formErrors = false
      let url = '/build-api/add/'
      let data = new FormData()
      data.append("image", this.image)
      if (! this.image.name ) {
        this.formErrors = true
      }
      data.append("title", this.title)
      data.append("intro", this.intro)
      data.append("lat", this.lat)
      this.formValidation(this.lat, "id_b_lat")
      data.append("long", this.long)
      this.formValidation(this.long, "id_b_long")
      data.append("zoom", this.zoom)
      this.formValidation(this.zoom, "id_b_zoom")
      if (this.formErrors) { return }//prevent from sending form
      axios
          .post(url, data)
          .then(response => {
            this.isAlertPanel = true
            if (this.title) {
              this.alert = this.title
            } else {
              this.alert = "New building"
            }
            this.isBuildList = true
            this.isBuildAdd = false
            this.clearData()
            this.render_buildings()
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
