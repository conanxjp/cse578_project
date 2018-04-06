/***************************************
 * Initial mapbox and leaflet setups   *
 ***************************************/
// mapbox public access token
var accessToken = "pk.eyJ1IjoiY29uYW54anAiLCJhIjoiY2pkcWluNnVqMXl1eTMzcWhwOG9pczVibCJ9.rO146qntrsOvvqxTqFrabg";
// initial map view position and zoom level
var map = L.map('map', {
  center: [40, -97],
  zoomSnap: 0.1,
  zoom: 4.6,
  minZoom: 4.6,
  maxZoom: 18
  // zoomControl: false
});
// map.fitWorld();
// set configurations of leaflet tile map layer using mapbox
L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=' + accessToken, {
    attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>',
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
var markers;
var business;
var stateList = d3.select('#state_list');
var cityList = d3.select('#city_list');
var restList = d3.select('#rest_list');
var STATE_ZOOM_LEVEL = 8;
var CITY_ZOOM_LEVEL = 10;
var DIR_BUSINESS = '../assets/data/business/';
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
  // console.log(e);
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
  cityList.selectAll('option').remove();
  var stateName = e.target.feature.properties.name;
  var center;
  var foundCapital = false;
  var rank = 1000;
  $('#state_list').val(state2abb[stateName]);
  var cities = [];
  if (cityContours) {map.removeLayer(cityContours);}
  cityContours = L.geoJson(citiesData, {
    filter: function(feature) {
      if (feature.properties.stateAbb === state2abb[stateName]) {
        cities.push(feature.properties.city);
        if (!foundCapital) {
          if (rank > feature.properties.rank) {
            rank = feature.properties.rank;
            center = [feature.properties.latitude, feature.properties.longitude];
          }
          if (feature.properties.CAPITAL === 'Y')
            foundCapital = true;
        }
      }
      return feature.properties.stateAbb === state2abb[stateName];
    },
    style: cityStyle,
    onEachFeature: onEachCityFeature
  }).addTo(map);
  cityList.selectAll('option')
            .data(cities)
            .enter()
            .append('option')
            .attr('value', function(c) {return c;})
            .text(function(c) {return c;});
  cityList.append('option')
            .attr('disabled', '').attr('selected', '').attr('value', '').text('-- select a city --');
  cityList.on('change', function() {zoomToCity()});
  map.setView(center, 8)
}

// define mouse click zoom effect for city
function zoomToCityFeature(e) {
  var cityInfo = e.target.feature.properties;
  var center = [cityInfo.latitude, cityInfo.longitude];
  var bounds = resizeBounds(e.target.getBounds(), 0.3)
  map.fitBounds(bounds, {paddingTopLeft: [bounds.getCenter().lat - center[0], bounds.getCenter().lng - center[1]], maxZoom: 12}); // padding to the right
  var state = cityInfo.stateAbb;
  var city = cityInfo.city;
  $('#city_list').val(city);
  addBusinessMarkers(state, city);
}

function zoomToCity() {
  city = $('#city_list').val()
  var cityInfo;
  citiesData.features.forEach(function(c) {
    if (c.properties.city == city) cityInfo = c.properties;
  });
  var center = [cityInfo.latitude, cityInfo.longitude];
  var state = cityInfo.stateAbb;
  map.setView(center, 12);
  addBusinessMarkers(state, city);
}

// redefine the bounds when city is selected to achieve desirable level of zoom
// factor defines how much to shrink the original bounds, takes value between 0 ~ 1
function resizeBounds(bounds, factor) {
  lng_diff = bounds._northEast.lng - bounds._southWest.lng;
  lat_diff = bounds._northEast.lat - bounds._southWest.lat;
  bounds._southWest.lng += factor * lng_diff;
  bounds._southWest.lat += factor * lat_diff;
  bounds._northEast.lng -= factor * lng_diff;
  bounds._northEast.lat -= factor * lat_diff;
  return bounds;
}

function addBusinessMarkers(state, city) {
  var businessJsonPath = DIR_BUSINESS + `${state}/${city}.json`;
  if (markers) {map.removeLayer(markers);}
  markers = L.markerClusterGroup({
    chunkedLoading: true,
    showCoverageOnHover: false,
    zoomToBoundsOnClick: true
  });
  // var regions = [];
  d3.json(businessJsonPath, function(error, data) {
    business = data;
    rankBusiness('name');
    addBusinessList();
    business.forEach(function(b, i) {
      marker = L.marker(L.latLng(b.latitude, b.longitude), {title: b.name});
      marker.bindPopup(b.name);
      // regions.push(marker);
      markers.addLayer(marker);
    });
  });
  // markers.addLayers(regions);
  map.addLayer(markers);
}

function rankBusiness(key) {
  business = business.sort((a, b) => d3.ascending(a.name, b.name));
}

function addBusinessList() {
  restList.selectAll('option')
            .data(business).enter()
            .append('option')
            .attr('value', function(b) {return b.business_id;})
            .text(function(b) {return b.name;});
  restList.on('change', selectRest);
}

function selectRest() {
  var businessId = $('#rest_list').val();
  var selectedBusiness = business.find(function(b) {return b.business_id == businessId;});
  hightlightMarker(selectedBusiness.name);
  
}

function hightlightMarker(name) {
  markers.eachLayer(function(m) {
    if (name === m.options.title) {
      markers.zoomToShowLayer(m, function() {m.openPopup();});
      return;
    }
  });
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

// add event listeners to city layer
function onEachCityFeature(feature, layer) {
  layer.on({
    mouseover: highlightFeature,
    mouseout: resetHighlight,
    click: zoomToCityFeature,
    dblclick: zoomOut
  });
}

function zoomToState(state) {
  cityList.selectAll('option').remove();
  var center;
  var foundCapital = false;
  var rank = 1000;
  // stateList.append('option').text(stateName);
  var cities = [];
  if (cityContours) {map.removeLayer(cityContours);}
  cityContours = L.geoJson(citiesData, {
    filter: function(feature) {
      if (feature.properties.stateAbb === state) {
        cities.push(feature.properties.city);
        if (!foundCapital) {
          if (rank > feature.properties.rank) {
            rank = feature.properties.rank;
            center = [feature.properties.latitude, feature.properties.longitude];
          }
          if (feature.properties.CAPITAL === 'Y')
            foundCapital = true;
        }
      }
      return feature.properties.stateAbb === state;
    },
    style: cityStyle,
    onEachFeature: onEachCityFeature
  }).addTo(map);
  cityList.selectAll('option')
            .data(cities)
            .enter()
            .append('option')
            .attr('value', function(c) {return c;})
            .text(function(c) {return c;});
  cityList.append('option')
            .attr('disabled', '').attr('selected', '').attr('value', '').text('-- select a city --');
  cityList.on('change', function() {zoomToCity()});
  map.setView(center, 8)
}

// initialized funciton
function init() {
  stateList.selectAll('option')
            .data(statesData.features).enter()
            .append('option')
            .attr('value', function(s) {return state2abb[s.properties.name];})
            .text(function(s) {return s.properties.name;});
            // .on('change', function() {console.log(+this.value);});
  stateList.append('option')
            .attr('disabled', '').attr('selected', '').attr('value', '').text('-- select a state --');
  stateList.on('change', function() {zoomToState($('#state_list').val());})
}

// add style and event listeners to each layer in GeoJson
states = L.geoJson(statesData, {
  style: stateStyle,
  onEachFeature: onEachStateFeature
}).addTo(map);  // add the configured GeoJson layer to map

init();

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
