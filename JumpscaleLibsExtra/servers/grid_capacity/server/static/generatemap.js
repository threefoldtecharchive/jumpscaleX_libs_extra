function generateUpdateMap(lat, lng){
    let mymap = L.map(`mapupdate`, {
        center:L.latLng(lat, lng),
        zoom:5
    });
    L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw', {
        maxZoom: 13,
        attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, ' +
            '<a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, ' +
            'Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
        id: 'mapbox.streets'
    }).addTo(mymap);
    
    function onMapClick(e) {
      L.popup()
            .setLatLng(e.latlng)
            .setContent("You clicked the map at " + e.latlng.toString())
            .openOn(mymap);
            sLat = e.latlng['lat'];
            sLng = e.latlng['lng'];
            $(`#updateFarmAddressInput`).val(sLat.toString() + "," + sLng.toString());
    }
    mymap.on('click', onMapClick);
    $(`#updatefarm`).on('shown.bs.modal', function(){
        setTimeout(function() {
          mymap.invalidateSize();
        }, 1);
       });

  }

function generateRegisterMap(){
  let lat = 51.260197;
  let lng =  4.402771;

  let mymap = L.map('mapregister').setView([lat, lng], 4);
  
  L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw', {
      maxZoom: 18,
      attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, ' +
          '<a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, ' +
          'Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
      id: 'mapbox.streets'
  }).addTo(mymap);

  let popup = L.popup();

  function onMapClick(e) {
      popup
          .setLatLng(e.latlng)
          .setContent("You clicked the map at " + e.latlng.toString())
          .openOn(mymap);
          sLat = e.latlng['lat'];
          sLng = e.latlng['lng'];
          $("#farmAddressInput").val(sLat.toString() + "," + sLng.toString());
  }
  mymap.on('click', onMapClick);
  $('#registerfarm').on('shown.bs.modal', function(){

      setTimeout(function() {
          mymap.invalidateSize();
      }, 1);
  });
}