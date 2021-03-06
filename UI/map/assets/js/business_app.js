/***************************************
 * Initial mapbox and leaflet setups   *
 ***************************************/
// mapbox public access token
var accessToken = "pk.eyJ1IjoiY29uYW54anAiLCJhIjoiY2pkcWluNnVqMXl1eTMzcWhwOG9pczVibCJ9.rO146qntrsOvvqxTqFrabg";
// initial map view position and zoom level
var map = L.map('map', {
  center: [37.8, -96],
  zoom: 4,
  minZoom: 4,
  maxZoom: 18
  // zoomControl: false
});
// map.fitWorld();
// set configurations of leaflet tile map layer using mapbox
L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=' + accessToken, {
    // attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>',
    maxZoom: 18,
    id: 'mapbox.streets'
}).addTo(map);

// map.on('click', function() {map.setView([37.8, -96],4);})

/***************************************
 * Style config for state shapes       *
 ***************************************/
// define color scale
function getStateColor(d) {
  return d > 1000 ? '#800026' :
         d > 500  ? '#BD0026' :
         d > 200  ? '#E31A1C' :
         d > 100  ? '#FC4E2A' :
         d > 50   ? '#FD8D3C' :
         d > 20   ? '#FEB24C' :
         d > 10   ? '#FED976' :
                    '#FFEDA0';
}

// define function to determine state fill color based on property
function stateStyle(feature) {
  return {

      weight: 2,
      opacity: 1,
      color: 'white',
      dashArray: '3',
      fillOpacity: 0.7,
      fillColor: getStateColor(feature.properties.density)
  };
}

/***************************************
 * Style config for city shapes       *
 ***************************************/
// define color scale
function getCityColor(d) {
  return d > 500000 ? '#800026' :
         d > 400000  ? '#BD0026' :
         d > 300000  ? '#E31A1C' :
         d > 200000  ? '#FC4E2A' :
         d > 150000   ? '#FD8D3C' :
         d > 50000   ? '#FEB24C' :
         d > 10000   ? '#FED976' :
                    '#FFEDA0';
}

// define function to determine state fill color based on property
function cityStyle(feature) {
  return {
      fillColor: getCityColor(feature.properties.POP2000),
      weight: 2,
      opacity: 1,
      color: 'white',
      dashArray: '3',
      fillOpacity: 0.7
  };
}


/***************************************
 * Add interactions                    *
 ***************************************/
var states;
var cityContours;
var MAX_CITIES = 300;
var test;
// define mouseover event handler
function highlightFeature(e) {
  // get mouse selected layer
  // console.log('city highlight');
  var layer = e.target;
  // set selected object/state styles
  layer.setStyle({
    weight: 5,
    color: '#666',
    dashArray: '',
    fillOpacity: 0.1
  });
  // multi-browser compatibilities
  if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
    layer.bringToFront();
  }
}
// define mouseover event handler
function highlightStateFeature(e) {
  // get mouse selected layer
  // console.log('state highlight');
  var layer = e.target;
  // set selected object/state styles
  layer.setStyle({
    weight: 5,
    color: '#666',
    dashArray: '',
    fillOpacity: 0.1
  });
  // multi-browser compatibilities
  // if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
  //   layer.bringToFront();
  // }
}
// define mouse our event handler
function resetHighlight(e) {
  // reset style to default defined in style config
  console.log(e);
  states.resetStyle(e.target);
}

// define mouse our event handler
function resetStateHighlight(e) {
  // reset style to default defined in style config
  // console.log('state reset');
  states.resetStyle(e.target);
}
// define mouse click zoom effect for state
function zoomToStateFeature(e) {
  map.fitBounds(e.target.getBounds(), {paddingTopLeft: [-300, -100], maxZoom: 10}); // padding to the right
  // map.removeLayer(states);
  // var polygon = e.target.feature.geometry.coordinates[0];
  // for (var i = 0; i < polygon.length; i ++) {
  //   polygon[i] = [polygon[i][1], polygon[i][0]];
  // }
  // test = polygon;
  // // console.log(polygon);
  // var stateContour = L.polygon(polygon, {
  //   style: stateStyle
  // }).addTo(map);
  var stateName = e.target.feature.properties.name;
  var center;
  if (cityContours) {map.removeLayer(cityContours);}
  cityContours = L.geoJson(citiesData, {
    filter: function(feature) {
      if (feature.properties.stateAbb === state2abb[stateName] && feature.properties.CAPITAL === 'Y')
        center = [feature.properties.latitude, feature.properties.longitude];
      return feature.properties.stateAbb === state2abb[stateName] && feature.properties.rank <= MAX_CITIES;
    },
    style: cityStyle,
    onEachFeature: onEachCityFeature
  }).addTo(map);
}

// define mouse click zoom effect for city
function zoomToCityFeature(e) {
  map.fitBounds(e.target.getBounds(), {paddingTopLeft: [-300, -100], maxZoom: 10}); // padding to the right
  // console.log('city zoom');
  // var state = e.target.feature.properties.name;
  // var center;
  // cityContours = L.geoJson(citiesData, {
  //   filter: function(feature) {
  //     if (feature.properties.stateAbb === state2abb[state] && feature.properties.CAPITAL === 'Y')
  //       center = [feature.properties.latitude, feature.properties.longitude];
  //     return feature.properties.stateAbb === state2abb[state] && feature.properties.rank <= MAX_CITIES;
  //   },
  //   style: cityStyle,
  //   onEachFeature: onEachCityFeature
  // }).addTo(map);
}

function zoomOut(e) {
  map.setView([37.8, -96], 4);
}


// add event listeners to state layer
function onEachStateFeature(feature, layer) {
  layer.on({
    mouseover: highlightStateFeature,
    mouseout: resetStateHighlight,
    click: zoomToStateFeature,
    dblclick: zoomOut
  });
}
// add style and event listeners to each layer in GeoJson
states = L.geoJson(statesData, {
  style: stateStyle,
  onEachFeature: onEachStateFeature
}).addTo(map);  // add the configured GeoJson layer to map


// add event listeners to city layer
function onEachCityFeature(feature, layer) {
  layer.on({
    mouseover: highlightFeature,
    mouseout: resetHighlight,
    click: zoomToCityFeature,
    dblclick: zoomOut
  });
}
// console.log(map);
// selected.addTo(map);

// console.log(test);
// map.setView([42.65258, -73.75623], 10)
// for (var i = 0; i < test.polygon.length; i ++) {
//   test.polygon[i] = test.polygon[i].reverse();
// }
//
// var polygon = L.polygon(test.polygon, {color: 'red'}).addTo(map);
// cities = L.geoJson(citiesData, {
//   filter: function(feature) {
//     // console.log(feature, d);
//     return feature.properties.STATEFP === stateFPs['AZ'];
//   }
// });

// var cityCenters = [];
// for (var i in cities._layers) {
//   cityCenters.push(cities._layers[i]);
// }

// cityCenters.sort((a, b) => a.feature.properties.ALAND < b.feature.properties.ALAND ? 1 : (a.feature.properties.ALAND > b.feature.properties.ALAND ? -1:0))
//
// cityCenters.slice(0,5).forEach(function(c, i) {
//   var point = c.feature.geometry.coordinates;
//   L.marker([point[1], point[0]]).addTo(map);
// });
