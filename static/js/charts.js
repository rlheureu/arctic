//
// Get performance data
// 
//

$.getJSON( "/componentfps", function( data ) {
	
	var fpsData = data.fps_data;
	
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
							fillcolor: 'rgba(44, 160, 101, 0.5)',
						    line: {
						    	color: 'rgb(44, 160, 101)'
						    }
						});
			trace1.x.push(dp.msrp);
			trace1.y.push(dp.fps_average - ((dp.fps_average - dp.fps_one)/2));
			trace1.text.push(dp.component_display_name);
			
			plottedPoints.push(dp);
		}

		layout = {
		  title: 'Genre: ' + genre,
		  xaxis: {
			  title: "FPS",
			  ticks: "inside",
			  zeroline: false
		  },
		  yaxis: {
			  title: "MSRP",
			  ticks: "inside",
			  showgrid: false
		  },
		  width: 650,
		  height: 390,
		  shapes: shapes,
		  hovermode: "closest"
		};

		var data = [trace1];

		Plotly.newPlot('tester', data, layout, {displayModeBar: false});
		
		document.getElementById('tester').on('plotly_hover', function(data){
			var dataIn = data;
			var pointNumber = data.points[0].pointNumber;		
			
			var path = $('#tester').find('path[data-index="' + pointNumber + '"]');
			var position = path.position();
			
			var dp = plottedPoints[pointNumber];
			var tt = $('<div id="helloCrazyDiv"><b>' + dp.component_display_name
					+ '</b><br><b>MSRP:</b> $' + dp.msrp
					+ '<br><b>Framerate:</b> <b>' + dp.fps_average +'</b> fps on average (<b>' + dp.fps_one + '</b> fps 99% of the time)'
					+ '<br><b>Benchmark:</b> ' + dp.benchmark_name
					+ '</div>');
			tt.css('position', 'fixed');
			tt.css('top', (position.top - 40) + 'px');
			tt.css('left', (position.left + 50) + 'px');
			tt.css('background-color', 'white');
			tt.css('border', '1px solid black');
			tt.css('padding', '10px');
			tt.css('z-index', 10000);
			$('body').append(tt);
			
			var xPos = data.points[0].x;
			var yPos = data.points[0].y;
			shapes[pointNumber].fillcolor = 'rgba(255, 15, 15, 0.5)';
			shapes[pointNumber].line.color = 'rgb(255, 15, 15)';
			Plotly.plot('tester', data, layout, {displayModeBar: false});
		}).on('plotly_unhover', function(data){
			var dataIn = data;
			var pointNumber = data.points[0].pointNumber;
			shapes[pointNumber].fillcolor = 'rgba(44, 160, 101, 0.5)';
			shapes[pointNumber].line.color = 'rgb(44, 160, 101)';
			
			
			$('#helloCrazyDiv').remove();
			
			Plotly.plot('tester', data, layout, {displayModeBar: false});
		});
	}
	
	renderChart('FPS');
	
	$('.genre-select-btn').click(function(){
		var genre = $(this).data('genre');
		$('.genre-select-btn').removeClass('active');
		$(this).addClass('active');
		renderChart(genre);
	})

});

