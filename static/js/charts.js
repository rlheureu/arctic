//
// Get performance data
// 
//

$.getJSON( "/componentfps", function( data ) {
	
	var fpsData = data.fps_data;
	
	function constructTooltipDiv(divName, dataPoint, shapePosition) {
		var tt = $('<div id="' + divName + '" class="chart-tt">'
				+ '<div><button class="btn pull-right" style="display:none" id="tt-close-button">Close</button></div>'
				+ '<div>'
				+ '<b class="fg-' + dataPoint.perf_color + '">' + dataPoint.component_display_name
				+ '</b><br><b>MSRP:</b> $' + dataPoint.msrp
				+ '<br><b>Framerate:</b> <b>' + dataPoint.fps_average
				+ '</b> fps on average (<b>' + dataPoint.fps_one + '</b> fps 99% of the time)'
				+ '<br><b>Benchmark:</b> ' + dataPoint.benchmark_name
				+ '</div>'
				+ '<div style="display:none" id="tt-equip-div"><hr><div><button>Examine</button><button>Equip</button></div></div>'
				+ '</div>');
		tt.css('top', (shapePosition.top - 40) + 'px');
		tt.css('left', (shapePosition.left + 50) + 'px');
		return tt;
	}
	
	function renderChart(genre){
		var shapes = [];
		var plottedPoints = [];
		
		var dataPoints = fpsData[genre] !== undefined ? fpsData[genre].datapoints : [];
		var minX = fpsData.x_range[0]
		var maxX = fpsData.x_range[1]
		var minY = fpsData.y_range[0]
		var maxY = fpsData.y_range[1]
		
		var trace1 = {
				  x: [],
				  y: [],
				  text: [],
				  mode: 'none',
				  hoverinfo: 'none'
				};
		
		for (i = 0; i < dataPoints.length; i++) {
			var dp = dataPoints[i];
			if (dp.svg_plot === null || dp.svg_plot === undefined || dp.svg_plot === "") continue;
			shapes.push({
							type : 'path',
							path : dp.svg_plot,
							fillcolor: dp.background_rgba,
						    line: {
						    	color: dp.outline_rgb
						    }
						});
			trace1.x.push('$' + dp.msrp);
			trace1.y.push(dp.fps_average - ((dp.fps_average - dp.fps_one)/2));
			trace1.text.push(dp.component_display_name);
			
			plottedPoints.push(dp);
		}
		layout = {
		  xaxis: {
			  title: "MSRP",
			  ticks: "inside",
			  showline : true,
			  gridcolor: "#333333"
		  },
		  yaxis: {
			  title: "FPS",
			  ticks: "inside",
			  showline : true,
			  gridcolor: "#333333"
		  },
		  margin: {
			  l:50,r:70,t:10,b:50,pad:15
		  },
		  width: 650,
		  height: 300,
		  shapes: shapes,
		  hovermode: "closest",
		  paper_bgcolor: 'rgba(0,0,0,0)',
		  plot_bgcolor: 'rgba(0,0,0,0)',
		  font : {
			  color:"#aaaaaa"
		  }
		};

		var data = [trace1];

		Plotly.newPlot('tester', data, layout, {displayModeBar: false});
		
		document.getElementById('tester').on('plotly_hover', function(data){
			
			if ($('#chart-tooltip-div').length) {
				// dialog is already visible do nothing
				return;
			}
			
			var dataIn = data;
			var pointNumber = data.points[0].pointNumber;		
			
			var path = $('#tester').find('path[data-index="' + pointNumber + '"]');
			var position = path.position();
			
			var dp = plottedPoints[pointNumber];
			var tt = constructTooltipDiv('chart-tooltip-div', dp, position);
			$('body').append(tt);
			
			var xPos = data.points[0].x;
			var yPos = data.points[0].y;
			shapes[pointNumber].fillcolor = 'rgba(255, 15, 15, 0.5)';
			shapes[pointNumber].line.color = 'rgb(255, 15, 15)';
			Plotly.plot('tester', data, layout, {displayModeBar: false});
			
			document.getElementsByClassName('nsewdrag')[0].style.cursor = 'pointer';
			
		}).on('plotly_unhover', function(data){
			var dataIn = data;
			var pointNumber = data.points[0].pointNumber;
			shapes[pointNumber].fillcolor = plottedPoints[pointNumber].background_rgba;
			shapes[pointNumber].line.color = plottedPoints[pointNumber].outline_rgb;
			
			$('html,body').css('cursor','');
			
			if (!$('#chart-tooltip-div').hasClass('clicked')) {
				$('#chart-tooltip-div').remove();
			}
			
			Plotly.plot('tester', data, layout, {displayModeBar: false});
			
			document.getElementsByClassName('nsewdrag')[0].style.cursor = '';
		}).on('plotly_click', function(data){
			$('#chart-tooltip-div').addClass('clicked');
			$('#tt-close-button').show();
			$('#tt-equip-div').show();
			$('#tt-close-button').click(function(){
				$('#chart-tooltip-div').remove();
			})
		});
	}
	
	// initially render FPS chart
	renderChart('FPS');
	
	$('.genre-select-btn').click(function(){
		var genre = $(this).data('genre');
		$('.genre-select-btn').removeClass('active');
		$(this).addClass('active');
		renderChart(genre);
	})

});

