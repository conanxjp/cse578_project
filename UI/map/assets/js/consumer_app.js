/***************************************
 * Initial mapbox and leaflet setups   *
 ***************************************/
// mapbox public access token
var accessToken = "pk.eyJ1IjoiY29uYW54anAiLCJhIjoiY2pkcWluNnVqMXl1eTMzcWhwOG9pczVibCJ9.rO146qntrsOvvqxTqFrabg";
// initial map view position and zoom level
var map = L.map('map', {
  center: [40, -97],
  zoomSnap: 0.1,
  zoom: 3.6,
  minZoom: 3.6,
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
var categoryBusiness = null;
var checkins;
var predefinedCategory = ["African", "American (New)", "American (Traditional)",
                  "Asian Fusion", "Bakeries", "Barbeque", "Bars", "Beverage",
                  "Breakfast", "Buffets", "Chinese", "Fast Food", "French",
                  "Greek", "Hawaiian", "Indian", "Italian", "Japanese",
                  "Korean", "Latin American", "Mediterranean", "Mexican",
                  "Middle Eastern", "Noodles", "Pizza", "Seafood", "Thai", "Vegetarian",
                  "Vietnamese"];
var categoryList = d3.select('#category_list');
var stateList = d3.select('#state_list');
var cityList = d3.select('#city_list');
var restList = d3.select('#rest_list');
var STATE_ZOOM_LEVEL = 8;
var CITY_ZOOM_LEVEL = 10;
var DIR_BUSINESS = '../assets/data/business_consumer/';
var DIR_CHECKIN = '../assets/data/checkin_consumer/';
var checkinWidth = 200//d3.select('#checkin').node().getBoundingClientRect().width;
var checkinHeight = 80; //d3.select('#checkin').node().getBoundingClientRect().height;
// var checkinHourScale = d3.time.scale().domain(function(d3.range()))
// var checkinHourScale = d3.scaleLinear().domain([0, 24]).range([0, checkinWidth * 0.9]);
// var checkinHourAxis = d3.axisBottom(checkinHourScale);
// checkinHourAxis.ticks(24);
// checkinHourAxis.tickValues(d3.range(3).map(i => i * 6 + 6));
var aspects = ['Food','Ambience','Price','Service', 'Misc'];
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
  addCityList(cities);

  map.setView(center, 8)
}

function addCityList(cities) {
  cityList.selectAll('option')
            .data(cities)
            .enter()
            .append('option')
            .attr('value', function(c) {return c;})
            .text(function(c) {return c;});
  cityList.append('option')
            .attr('disabled', '').attr('selected', '').attr('value', '').text('-- select a city --');
  cityList.on('change', function() {zoomToCity()});
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
  loadBusiness(state, city);
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
  loadBusiness(state, city);
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

function loadBusiness(state, city) {
  var businessJsonPath = DIR_BUSINESS + `${state}/${city}_business_final.json`;
  d3.json(businessJsonPath, function(error, data) {
    var categories = getCategories(data);
    business = updateScore(data);
    business = rankBusiness(business);
    addBusinessMarkers();
    addCategoryList(categories);
  });
  loadCheckin(state, city);
}

function getCategories(business) {
  var categories = new Set();
  business.forEach(function(b) {
    b.categories.forEach(function(c) {
      if (predefinedCategory.indexOf(c) >= 0)
        categories.add(c);
    });
  });
  return Array.from(categories);
}

function addBusinessMarkers() {
  if (markers) {map.removeLayer(markers);}
  markers = L.markerClusterGroup({
    chunkedLoading: true,
    showCoverageOnHover: false,
    zoomToBoundsOnClick: true
  });
  var regions = [];
  addBusinessList(business);
  business.forEach(function(b, i) {
    marker = L.marker(L.latLng(b.latitude, b.longitude), {title: b.name, id: b.business_id});
    marker.bindPopup(b.name);
    marker.on('click', function() {highlightSelection(b.business_id);});
    regions.push(marker);
  });
  markers.addLayers(regions);
  map.addLayer(markers);
  map.fitBounds(markers.getBounds());
}

function updateScore(data) {
  var aspectWeights = [];
  aspects.forEach(function(a) {
    var aspect = '#' + `${a}`;
    aspectWeights.push(d3.select(aspect).property('value'))
  });
  data.map(function(b) {
    b.score = 0;
    aspects.forEach(function(a, i) {
      b.score += b[a.toLowerCase()] * aspectWeights[i];
    });
  });
  return data;
}

function updateStars(data) {
  var sum = 0;
  data.forEach(function(b) {
    sum += b.score
  });
  data.map(function(b, i) {
    b.stars_p = b.stars_x + (b.score - sum/data.length) / sum;
    if (b.stars_p > 5 || b.stars_p < 0) {
        b.stars_p = b.stars_p > 5 ? 5 : b.stars_p;
        b.stars_p = b.stars_p < 0 ? 0 : b.stars_p;
    }
  });
  return data;
}

function dispStar(selectedBusiness) {
  d3.select('#stars').remove();
  var stars = Math.round(selectedBusiness.stars_p * 10) / 10;
  console.log(selectedBusiness);
  d3.select('#review_star').append('label').attr('id', 'stars').text('Rating: ' + `${stars}` + '/5.0')
}

function rankBusiness(data) {
  return data.sort((a, b) => d3.descending(a.score, b.score));
}

function addBusinessList(businessList) {
  restList.selectAll('option').remove();
  restList.selectAll('option')
            .data(businessList).enter()
            .append('option')
            .attr('value', function(b) {return b.business_id;})
            .text(function(b) {return b.name;});
  restList.on('change', selectRest);
}

function selectRest() {
  var businessId = $('#rest_list').val();
  var selectedBusiness = business.find(function(b) {return b.business_id == businessId;});
  highlightMarker(businessId);
  showCheckin(businessId);
  drawWordCloud(selectedBusiness['good words'], true);
  drawWordCloud(selectedBusiness['bad words'], false);
  data = categoryBusiness;
  if (!categoryBusiness) {
    data = business;
  }
  updateStars(data);
  dispStar(selectedBusiness);
}

function highlightMarker(bid) {
  markers.eachLayer(function(m) {
    if (bid === m.options.id) {
      markers.zoomToShowLayer(m, function() {m.openPopup();});
      map.setView([m._latlng.lat, m._latlng.lng], 18);
      return;
    }
  });
}

function loadCheckin(state, city) {
  var checkinJsonPath = DIR_CHECKIN + `${state}/${city}/${city}_checkin.json`;
  d3.json(checkinJsonPath, function(error, data) {
    checkins = data;
  });
}

function showCheckin(businessId) {
  d3.select('#checkin svg').remove();
  var checkinSvg = d3.select('#checkin').append('svg').attr('width', 220);
  var day = 'Monday';
  var hoursInt = d3.range(24);
  var hours = [];
  hoursInt.forEach(function(h) {hours[`${h}:00`] = 0;});
  var checkinHourScale = d3.scaleLinear().domain([0, 23]).range([0, checkinWidth * 0.9]);

  var checkinHourAxis = d3.axisBottom(checkinHourScale);
  checkinHourAxis.tickValues(d3.range(24));
  if (checkins[businessId]) {
    var checkin = checkins[businessId][day]
    if (checkin) {
      max = 5
      for (var hour in checkin) {
        if (checkin[hour] > max) max = checkin[hour];
        hours[hour] = checkin[hour];
      }
      hour = []
      for (var key in hours) {
        hour.push(hours[key]);
      }
      var checkinCountScale = d3.scaleLinear().domain([max, 0]).range([0, checkinHeight * 0.8]);
      var checkinCountAxis = d3.axisLeft(checkinHourScale);
      // checkinCountAxis.tickValues(d3.range(max));
      var checkinYAxis = checkinSvg.append('g')
                                  .attr('id', 'checkin_y_axis')
                                  .attr('transform', 'translate(5, 0)')
                                  .transition()
                                  .duration(500)
                                  .call(checkinCountAxis);;
      var checkinXAxis = checkinSvg.append('g')
                                  .attr('id', 'checkin_x_axis')
                                  .attr('transform', 'translate(5, 120)')
                                  .transition()
                                  .duration(500)
                                  .call(checkinHourAxis);;

      checkinSvg.append('text')
                  .attr('id', 'checkin_x_axis_label')
                  .attr('transform', 'translate(100, 150)')
                  .style('text-anchor', 'middle')
                  .attr('font-size', '0.5em')
                  .text('Hour');
      console.log(hour);
      var bandwidth = checkinWidth * 0.9 / 24;
      var checkinBars = checkinSvg.append('g')
                              .attr('id', 'checkin_bars')
                              .attr('transform', 'translate(5, 55)');
      checkinBars.selectAll('rect')
                  .data(hour).enter()
                  .append('rect')
                  .attr('x', function(d, i) {return checkinHourScale(i);})
                  .attr('height', function(d) {return checkinHeight * 0.8 - checkinCountScale(d);})
                  .attr('width', bandwidth)
                  .transition()
                  .duration(500)
                  .attr('y', function(d) {return checkinCountScale(d);});
    }
    else {
      // TODO closed picture
    }
  }
  else {
    // console.log(businessId);
  }
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
  addCityList(cities);
  map.setView(center, 8)
}

function addCategoryList(categories) {
  categoryList.selectAll('option').remove();
  categoryList.selectAll('option')
                .data(categories).enter()
                .append('option')
                .attr('value', function(c) {return c;})
                .text(function(c) {return c;});
  categoryList.append('option')
                .attr('selected', '')
                .attr('value', 'all')
                .text('All');
  categoryList.on('change', filterCategory);
}

function filterCategory() {
  var category = $('#category_list').val();
  categoryBusiness = business.filter(function(b) {
    return b.categories.constructor === Array ? b.categories.includes(category) : b.categories === category;
  });
  if (categoryBusiness.length != 0) {
    addFilteredBusinessMarkers(categoryBusiness);
  }
  // TODO
  else {
    restList.selectAll('option').remove();
    var msg = 'Sorry! No ' +`${category}` + ' available in this area';
    restList.append('option').text(msg);
    console.log('no results category');
  }
}

function addFilteredBusinessMarkers(filteredBusiness) {
  addBusinessList(filteredBusiness);
  if (markers) {map.removeLayer(markers);}
  markers = L.markerClusterGroup({
    chunkedLoading: true,
    showCoverageOnHover: false,
    zoomToBoundsOnClick: true
  });
  var regions = [];
  filteredBusiness.forEach(function(b) {
    var marker = L.marker(L.latLng(b.latitude, b.longitude), {title: b.name, id: b.business_id});
    marker.bindPopup(b.name);
    marker.on('click', function() {highlightSelection(b.business_id);});
    regions.push(marker);
    // markers.addLayer(marker);
  });
  // TODO not centered at the selected marker
  if (regions.length == 1) {
    markers.addLayer(marker);
    // marker.openPopup();
    // console.log(filteredBusiness[0].business_id);
    // highlightMarker(filteredBusiness[0].business_id);
  }
  markers.addLayers(regions);
  map.addLayer(markers);
  // map.fitBounds(markers.getBounds());
}

function highlightSelection(bid) {
  showCheckin(bid);
  data = categoryBusiness;
  if (!categoryBusiness) {
    data = business
  }
  selectedBusiness = data.find(function(b) {return b.business_id == bid;});
  drawWordCloud(selectedBusiness['good words'], true);
  drawWordCloud(selectedBusiness['bad words'], false);
  var selected = restList.selectAll('option')
            .filter(function(o) {return o.business_id === bid})
            .attr('selected', '');
}

function addFilterSliders() {
  var controls = d3.select('#filter_controls');
  controls.selectAll('input')
          .data(aspects).enter()
          .append('label').attr('class', 'slider_label').text(function(a) {return a;})
          .append('input')
          .attr('type', 'range')
          .attr('min', -0)
          .attr('max', 1)
          .attr('step', 0.1)
          .attr('value', 0.5)
          .attr('id', function(a) {return a})
          .attr('class', 'slider')
          .on('input', sliderFunction);
}

function sliderFunction() {
  var data = null;
  if (!categoryBusiness) {
    data = business;
  }
  else {
    data = categoryBusiness;
  }
  updateScore(data);
  data = rankBusiness(data);
  addBusinessList(data);
}

var testButton = d3.select('#test_button').on('click', testfunc);

function testfunc() {
  updateStars(business);
  business.forEach(function(b) {
    console.log(b.stars_p);
  });
}


function drawWordCloud(restWords, isGood) {
  if (restWords == null) {
    // TODO draw unavailable
    return;
  }
  var wordCloudId = '#good_word_cloud';
  var wordCloudSvgId = "good_wc_svg";
  if (!isGood) {
    wordCloudId = '#bad_word_cloud';
    wordCloudSvgId = "bad_wc_svg";
  }
  var total = Object.values(restWords).reduce((a, b) => a + b, 0);
  var fill = d3.scaleOrdinal(d3.schemeCategory20);
  var layout = d3.layout.cloud()
                  .size([200, 200])
                    .words(Object.keys(restWords).map(function(d) {
      return {text: d, size: 10 + restWords[d] / total * 10, test: "haha"};
    }))
    .padding(5)
    .rotate(function() { return ~~(Math.random() * 2) * 90; })
    .font("Impact")
    .fontSize(function(d) { return d.size; })
    .on("end", draw);

  layout.start();

  function draw(words) {
    d3.select('#' + wordCloudSvgId).remove();
    d3.select(wordCloudId).append("svg")
    .attr("id", wordCloudSvgId)
    .attr("width", layout.size()[0])
    .attr("height", layout.size()[1])
    .append("g")
    .attr("transform", "translate(" + layout.size()[0] / 2 + "," + layout.size()[1] / 2 + ")")
    .selectAll("text")
    .data(words)
    .enter().append("text")
    .style("font-size", function(d) { return d.size + "px"; })
    .style("font-family", "Impact")
    .style("fill", function(d, i) { return fill(i); })
    .attr("text-anchor", "middle")
    .attr("transform", function(d) {
      return "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")";
    })
    .text(function(d) { return d.text; });
  }
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
  addFilterSliders();
}

// add style and event listeners to each layer in GeoJson
states = L.geoJson(statesData, {
  style: stateStyle,
  onEachFeature: onEachStateFeature
}).addTo(map);  // add the configured GeoJson layer to map

init();
