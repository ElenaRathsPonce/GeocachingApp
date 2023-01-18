var mapa = new ol.Map({
  target: 'mapa',
  layers: [
    new ol.layer.Tile({
      source: new ol.source.OSM()
    })
  ],
  view: new ol.View({
    center: ol.proj.fromLonLat([2, 40]),
    zoom: 4
  })
});

mapa.on('singleclick', function(event) {
  var coordinate = event.coordinate;
  var lonLat = ol.proj.toLonLat(coordinate);
  var lon = lonLat[0];
  var lat = lonLat[1];
  
  addMarker(lon,lat);  
});

function getCoordinates() {  
  lista = [];
  lista.push(mapa.getView().getCenter());
  lista.push(mapa.getView().getZoom());
  lista.push("algo");
  return "lista";
}

function setCoordinates() {
  var lat = document.getElementById("lat").value;
    var lng = document.getElementById("lng").value;
    var view = mapa.getView();
    var center = ol.proj.fromLonLat([lng, lat]);
    view.setCenter(center);
    view.setZoom(16);
}

function goToPlace() {
  var inputPlace = document.getElementById("inputPlace").value;
  var url = 'https://nominatim.openstreetmap.org/search?q=' + inputPlace + '&format=json&limit=1';

  fetch(url)
  .then(response => response.json())
  .then(data => {
    var lat = data[0].lat;
    var lon = data[0].lon;
    var view = mapa.getView();
    var center = ol.proj.fromLonLat([lon, lat]);
    view.setCenter(center);
    view.setZoom(16);
  })
  .catch(error => console.log(error));
}

function addMarker(lng,lat) {

  // Inicializa el mapa en el elemento DIV con las coordenadas en el centro
  var map = L.map('mapa').setView([lat, lng], 13);

  // Agrega una capa de OpenStreetMap al mapa
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);

  // Agrega el marcador al mapa en las coordenadas específicas
  var marker = L.marker([lat, lng]).addTo(map);
}

if (navigator.geolocation) {
  navigator.geolocation.getCurrentPosition(function(position) {
    var pos = {
      lat: position.coords.latitude,
      lng: position.coords.longitude
    };
    var view = mapa.getView();
    var center = ol.proj.fromLonLat([pos.lng, pos.lat]);
    view.setCenter(center);
    view.setZoom(16);
  }, function() {
    handleLocationError(true, infoWindow, map.getCenter());
  });
} else {
  handleLocationError(false, infoWindow, map.getCenter());
}