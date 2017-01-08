queue()
    .defer(d3.json, "/data")
    .await(makeGraphs);

function makeGraphs(error, recordsJson) {
	
	//Clean data
	var records = recordsJson;
	var dateFormat = d3.time.format("%Y-%m-%d %H:%M:%S");
	
	records.forEach(function(d) {
		d["time"] = dateFormat.parse(d["time"]);
		d["time"].setMinutes(0);
		d["time"].setSeconds(0);
		d["lon"] = +d["lon"];
		d["lat"] = +d["lat"];
	});

	//Create a Crossfilter instance
	var ndx = crossfilter(records);

	//Define Dimensions
	var dateDim = ndx.dimension(function(d) { return d["time"]; });
	var countryDim = ndx.dimension(function(d) { return d["country"]; });
	var allDim = ndx.dimension(function(d) {return d;});


	//Group Data
	var numRecordsByDate = dateDim.group();
	var countryGroup = countryDim.group();
	var all = ndx.groupAll();


	//Define values (to be used in charts)
	var minDate = dateDim.bottom(1)[0]["time"];
	var maxDate = dateDim.top(1)[0]["time"];


    //Charts
	var timeChart = dc.barChart("#time-chart");
	var locationChart = dc.rowChart("#location-row-chart");


	timeChart
		.width(1250)
		.height(140)
		.margins({top: 10, right: 50, bottom: 20, left: 20})
		.dimension(dateDim)
		.group(numRecordsByDate)
		.transitionDuration(500)
		.x(d3.time.scale().domain([minDate, maxDate]))
		.elasticY(true)
		.yAxis().ticks(0);


    locationChart
    	.width(500)
		.height(500)
        .dimension(countryDim)
        .group(countryGroup)
        .ordering(function(d) { return -d.value })
        .colors(['#6baed6'])
        .elasticX(true)
        .labelOffsetY(10)
        .xAxis().ticks(0);

    var map = L.map('map');

	var drawMap = function(center, zoom){
	    map.setView(center, zoom);
		mapLink = '<a href="http://openstreetmap.org">OpenStreetMap</a>';
		L.tileLayer(
			'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
				attribution: '&copy; ' + mapLink + ' Contributors',
				maxZoom: 15,
			}).addTo(map);

		//HeatMap
		var geoData = [];
		_.each(allDim.top(Infinity), function (d) {
			geoData.push([d["lat"], d["lon"], 1]);
	      });
		var heat = L.heatLayer(geoData,{
			radius: 10,
			blur: 20, 
			maxZoom: 1,
		}).addTo(map);
	};

	//Draw Map
	drawMap([0, 0], 1);


	//Update the heatmap if any dc chart get filtered
	dcCharts = [timeChart, locationChart];

	_.each(dcCharts, function (dcChart) {
		dcChart.on("filtered", function (chart, filter) {
			map.eachLayer(function (layer) {
				map.removeLayer(layer)
			});
			var center = map.getCenter()
            var zoom = map.getZoom()
			drawMap(center, zoom);
		});
	});

	dc.renderAll();

};