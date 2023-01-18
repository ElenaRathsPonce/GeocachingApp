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