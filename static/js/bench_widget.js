//initialize rig (local storage)
var currentRig = {};
currentRig['parts'] = currentRig['parts'] || {};
$(function(){
		
	// set cube name
	currentRig['name'] = (AC_GLOBALS.cubeName !== null) ? AC_GLOBALS.cubeName : 'Cube Name';
	
	// blank rig (new rig with no owner)
	var blankRig = (AC_GLOBALS.rig === null);
	
	// prepare preset values
	if (AC_GLOBALS.preset !== null) {
		populateRigById(AC_GLOBALS.preset);
	} else if (AC_GLOBALS.rig !== null) {
		populateRigById(AC_GLOBALS.rig);
		currentRig['rig_id'] = AC_GLOBALS.rig; // set ID for subsequent saves to update
	} else {
		// initial render
		refreshPartsCache(renderRig);
	}
	
	if (AC_GLOBALS.upgrade !== null) {
		populateRigById(AC_GLOBALS.upgrade);
		currentRig['upgrading'] = AC_GLOBALS.upgrade; // which cube we are upgrading
		if (AC_GLOBALS.upgradeName !== null) currentRig['upgradingName'] = AC_GLOBALS.upgradeName;
	}
	
	// set the usage in the model
	if (AC_GLOBALS.use !== null) {
		currentRig['use'] = AC_GLOBALS.use;
		currentRig['owned'] = AC_GLOBALS.use === 'owned';
	}
	
	// initialize edited functionality
	// hide all "edited" labels
	$('.label-edited').hide();
	currentRig['edited'] = {};
	
	function populateRigById(rigId){
		//
		//
		// GET RIG INFO, SET, AND RENDER
		$.getJSON( "getrig", {rig_id: rigId}).success(function(data) {
			var presetRig = JSON.parse(data.rig);
			console.log(presetRig);
			if (presetRig['motherboard_component_id'] !== undefined) currentRig['parts']['motherboard_id'] = presetRig['motherboard_component_id'];
            if (presetRig['gpu_component_id'] !== undefined) currentRig['parts']['gpu_id'] = presetRig['gpu_component_id'];
            if (presetRig['memory_component_id'] !== undefined) currentRig['parts']['memory_id'] = presetRig['memory_component_id'];
            if (presetRig['display_component_id'] !== undefined) currentRig['parts']['display_id'] = presetRig['display_component_id'];
            if (presetRig['cpu_component_id'] !== undefined) currentRig['parts']['cpu_id'] = presetRig['cpu_component_id'];
            if (presetRig['power_component_id'] !== undefined) currentRig['parts']['power_id'] = presetRig['power_component_id'];
            if (presetRig['storage_component_id'] !== undefined) currentRig['parts']['storage_id'] = presetRig['storage_component_id'];
            if (presetRig['chassis_component_id'] !== undefined) currentRig['parts']['chassis_id'] = presetRig['chassis_component_id'];
            refreshPartsCache(renderRig);
		});
	}
	
	//
	//
	// initialization complete
	// set up bindings etc.
	//
	//
	
	//
	// Enable editing the name if you own this rig, or if it's a new rig
	//
	if((AC_GLOBALS.myRig && AC_GLOBALS.rig) || !AC_GLOBALS.rig) {
		$('#bench-cube-title').css('cursor','pointer');
		$('#bench-cube-title').click(function(){
			$('#edit-name-modal').modal('show');
			$('#change-name-input').val(currentRig.name);
		});
	}
	$('#save-name-change-button').click(function(){
		$('#edit-name-modal').modal('hide');
		currentRig.name = $('#change-name-input').val();
		currentRig['miscEdited'] = true;
		renderRig();
	});
	
	$('#save-cube-button').click(function(){
		// if the user is logged in this link will click off save
		// else the user will need to register before they can save
		ArcticBasics.isLoggedIn(saveCubePrompt, function(){
			// not logged in
			ArcticBasics.initLogin(saveCubePrompt);
		});
	});
	
	$('#own-this-button').click(function(){
		
		// unchecked will be visible if user intends to mark as owned
		var toggleOwned = $('#owned_uncheck').is(":visible");
		var useStr = toggleOwned ? 'owned' : 'other';
		
		if (useStr === 'owned') {
			currentRig['owned'] = true;
			$('#owned_check').show();
			$('#owned_uncheck').hide();
		} else {
			currentRig['owned'] = false;
			$('#owned_check').hide();
			$('#owned_uncheck').show();
		}
		
		currentRig['miscEdited'] = true;
		renderRig();
		
		
	});
	
	function saveCubePrompt(){
		
		// Rig already exists and has not been edited.. continue save
		if (currentRig.rig_id !== undefined && Object.keys(currentRig['edited']).length === 0){
			continueSave();
			return;
		}
		
		// rig exists - check to see which parts have been edited
		// show the user which part is changing
		if (currentRig.rig_id !== undefined) {
			// determine the edited parts
			$('#owned-parts-list').empty();
			var addingNewPart = false;
			for (comp in currentRig['edited']) {
				var partId = currentRig['parts'][comp + '_id'];
				if( $.inArray(partId, AC_GLOBALS.unequippedParts) < 0) {
					addingNewPart = true;
					var text = $('.ac-' + comp + '-section').find('.part-item-title').text();
					if (text && text !== '') $('#owned-parts-list').append('<div class="added-owned-part">' + text + '</div>');
				}
			}
			if (addingNewPart && currentRig.owned)
				$('#add-owned-parts-modal').modal('show');
			else
				continueSave();
		} else {
			//
			// otherwise prompt user with question about rig ownership
			// if this rig is a new rig
			$('#rig-type-modal').modal('show');
		}
		
	}
	
	$('.continue-save-btn').click(continueSave);
	
	function continueSave(){
		var postRig = currentRig['parts'];
		postRig['name'] = currentRig['name'];
		postRig['owned'] = currentRig['owned'] && currentRig['owned'] === true;
		if (currentRig.rig_id !== undefined) postRig['rig_id'] = currentRig.rig_id;
		
		$.post('/savecube', postRig).success(function(data){
			window.location.href = '/bench?rig=' + data.rig_id;
		});
	}
	
	function resetCube(){
	    currentRig = {};
	    currentRig['parts'] = {};
	    renderRig();
	}
	
	// selected item prior to save
	var toEquip = null;
	var equipType = null;
	
	// initialize parts cache with part data by id
	var partsCache = {};
	
	//
	// dismiss modal after saving
	//
	$('#modal-save-btn').click(function(){
		
		// if toEquip is null
		if (toEquip !== null) {
			// set edited part
			var currEquipId = currentRig['parts'][equipType + '_id'];
			if (currEquipId !== toEquip) currentRig['edited'][equipType] = true; // edited part
			
			// set part to equip in view
			console.log('equip ' + equipType + ' ' + toEquip);
			currentRig['parts'][equipType + '_id'] = toEquip;	
		}
		
		$('#part-item-list').empty();
		$('#part-item-list').hide();
		$('#pick-part-modal').modal('hide');
		renderRig();
	});
	
	$('#modal-unequip-btn').click(function(){
		console.log('unequip ' + equipType);
		currentRig['parts'][equipType + '_id'] = null;
		$('#part-item-list').empty();
		$('#part-item-list').hide();
		$('#pick-part-modal').modal('hide');
		renderRig();
	});
	
	//
	// dismiss modal (cancel)
	//
	$('#modal-cancel-btn').click(function(){
		$('#part-item-list').empty();
		$('#part-item-list').hide();
		$('#pick-part-modal').modal('hide');
	});
	
	//
	// equip buttons - show modal and load parts
	//
	if(AC_GLOBALS.myRig || blankRig) {
		$('.equipbutton').click(renderPartPickerModal);
		$('.equip-clickable').click(renderPartPickerModal);
	} else {
		$('.equip-clickable').css('cursor', 'auto');
	}

	//
	// Search when any serach input changes, hook up event listeners
	//
	var searchStrTimeout = null;
	$('#search-parts-input').keyup(function(e){
		
		$('.ppm-loading-spinner').show();
		
		var inVal = $(this).val();
		var keyCode = e.which;
		
		if (searchStrTimeout) clearTimeout(searchStrTimeout);
		if (e.which == 13 || inVal.length == 0) {
			// enter key, go ahead and search
			searchPartsAndRenderResult();
		} else if ((keyCode >= 48 && keyCode <= 90) || keyCode == 8) {
			searchStrTimeout = setTimeout(searchPartsAndRenderResult, 750);
		}
	});
	$('#search-show-only-compat-parts').change(function(){ searchPartsAndRenderResult(); });
	$('#search-rank-select').change(function(){ searchPartsAndRenderResult(); });
	$('#search-manufacturer-select').change(function(){ searchPartsAndRenderResult(); });

	function searchPartsAndRenderResult() {
		
		$('.ppm-loading-spinner').show();
		
		var searchPartsParams = {};
		searchPartsParams.target = equipType;
		searchPartsParams.q = $('#search-parts-input').val();
		searchPartsParams.rank = $('#search-rank-select').val();
		searchPartsParams.manufacturer = $('#search-manufacturer-select').val();
		$.extend(searchPartsParams, currentRig['parts']);

		if($('#search-show-only-compat-parts').is(':checked')) {
			searchPartsParams.compat = $('#search-show-only-compat-parts').is(':checked')
		}

		var currentEquippedId = currentRig['parts'][equipType + '_id'];
		
		$.getJSON( "/parts/search", searchPartsParams).success(function(data) {
        	
        	renderFromPartsList(data, currentEquippedId);
        	
        	bindEquipListener();
        	
        	$('.ppm-loading-spinner').hide();

        }).fail(function() {
            console.log( "error" );
        });
	}
	
	function renderChartForType(componentEType){
		$('#coming-soon-chart-container').hide();
		$('#part-picker-tabs').show();
		//if (componentEType === 'cpu') {
		//	$('#cpu-chart-container').show();
		//}
		//else {
			$('#part-picker-tabs').hide();
			$('#cpu-chart-container').hide();
			$('#coming-soon-chart-container').show();
		//}
	}
	
	//
	// Rendering PART PICKER MODAL
	//
	function renderPartPickerModal() {
		
		$('.ppm-loading-spinner').show();
		
		var eType = $(this).parent().data('equip-type');
		equipType = eType;
		
		//
		// show the chart
		renderChartForType(eType);
		
		//
		// Always show the list by default
		$('#part-item-list-tab').tab('show'); 
		
		//
		// clear out search options
		$('#search-manufacturer-select').html('<option value="">All Manufacturers</option>');
		$('#search-rank-select').val('');
		$('#search-parts-input').val('');
		$('#search-show-only-compat-parts').prop('checked', false);
		
		//
		// clear out any previously selected parts
		toEquip = null;
		
		//
		// set title
		var equipTitle = $(this).parent().data('equip-title');
		$('#equip-modal-title').html(equipTitle);
		
		var currentEquippedId = currentRig['parts'][eType + '_id'];
        
        // Call server with datatype and current PC config
        var getPartsParams = {};
        getPartsParams.target = eType;
        $.extend(getPartsParams, currentRig['parts']);
        $.getJSON( "/widgetgetparts", getPartsParams).success(function(data) {
        	
        	renderFromPartsList(data, currentEquippedId);
        	
        	bindEquipListener();
        	
        	$('.ppm-loading-spinner').hide();
        	
        	$('#part-item-list').slideDown(800);
        	
        }).fail(function() {
            console.log( "error" );
        });

		$.getJSON( "/manufacturers/get", {target: eType}).success(function(data) {
        	
        	for(var i=0;i<data.length;i++){
        		$('#search-manufacturer-select').append(
        			'<option value="' + data[i] + '">' + data[i] + '</option>'
        		);
        	}

        }).fail(function() {
            console.log( "error" );
        });
		
		//$('#pick-part-modal').modal('show');
	}

	function constructFpsTable(fpsDataTable){
		//
		var tableHtml = '<table>';
		var columns = 1;
		if (fpsDataTable.column_headers) {
			tableHtml += '<tr><td><b>Avg FPS</b></td>';
			for (var i=0; i<fpsDataTable.column_headers.length; i++) {
				tableHtml += '<td class="fps-table-header">' + fpsDataTable.column_headers[i] + '</td>';
				columns += 1;
			}
			tableHtml += '</tr>';
		} else {
			tableHtml = '<b>Avg FPS</b><br>' + tableHtml;
		}
		
		for (var i=0; i<fpsDataTable.values.length; i++) {
			var tableRow = fpsDataTable.values[i];
			tableHtml += '<tr><td class="fps-table-row-title">' + tableRow.name + '</td>';
			for (var j=0; j<tableRow.values.length;j++) {
				tableHtml += '<td class="fps-table-row-value" style="color:'+tableRow.values[j].color+';">' + tableRow.values[j].text + '</td>';
			}
			tableHtml += '</tr>'
		}
		
		if (fpsDataTable.sources) {
			var srcStr = '';
			for (var i=0; i<fpsDataTable.sources.length; i++) {
				srcStr += fpsDataTable.sources[i] + (i < fpsDataTable.sources.length - 1 ? ', ' : '');
			}
			tableHtml += '<tr><td colspan="' + columns + '">Sources: ' + srcStr + '</td></tr>';
		}
		
		tableHtml += '</table>';
		
		return '<br>' + tableHtml;
	}
	
	function constructPartItemContentDiv(component){
		
		var contentDiv = $('<div class="row"></div>');
		
		// content on left
		var contentLeft = $('<div class="col-xs-8 col-md-10"></div>');
		var titleSpan = $('<span class="part-item-title">' + constructDisplayName(component) + '</span>');
		contentLeft.append(titleSpan);
		if (component.compatible === true) {
			contentLeft.append('<span class="part-item-sub">' + constructPerformanceNote(component) + '</span>');
			titleSpan.addClass('fg-' + component.perf_color);	// style title span
		} else {
			contentLeft.append('<span class="part-item-sub fg-inc-red">INCOMPATIBLE</span>'); // incompatible text
			titleSpan.addClass('fg-inc'); 	// title color
		}
		
		if (component.fps_data_table) {
			// FOR WIDGET DO NOT RENDER THIS
			//var fpsTable = constructFpsTable(component.fps_data_table);
			//contentLeft.append(fpsTable);
		}
		
		// content on right
		var contentRight = $('<div class="col-xs-4 col-md-2"></div>');
		if (component.priceformatted) {
			contentRight.append('<span class="part-item-price">' + component.priceformatted + '</span><br><small>On Amazon</small>');
		} else {
			contentRight.append('<span class="part-item-unavailable">Component not available</span>');
		}
		var labels = $('<br><br><span class="label ppm-label ppm-label-equipped">Selected</span><br><br><span class="label ppm-label ppm-label-recommended">RECOMMENDED</span>&nbsp;&nbsp;&nbsp;&nbsp;</div>');
		contentRight.append(labels);
		
		// wrap up
		contentDiv.append(contentLeft).append(contentRight);
		return contentDiv;
	}
	
	function renderFromPartsList(data, currentEquippedId) {
		var itemListView = $('#part-item-list');
    	itemListView.empty();
    	
		var partsList = data;
    	for (part in partsList) {	        		
    		var component = partsList[part];
    		
    		//
    		// add to parts cache (needed later)
    		partsCache[component.id] = component;
    		
			var itemDiv = $('<div class="equip-part-item row"></div>');
			var contentDiv = $('<div class="part-item-content col-xs-12"></div>');
			contentDiv.append(constructPartItemContentDiv(component));
			
			var equippedLabel = contentDiv.find('.ppm-label-equipped').hide();
			var recommendedLabel = contentDiv.find('.ppm-label-recommended').hide();
			
			itemDiv.append(contentDiv);
			
			//
			// set component ID
			//
			itemDiv.attr('data-component-id', component.id);
			
			// style current equipped if exists
			if (currentEquippedId === component.id) {
				equippedLabel.show();
			}
			
			if (component.compatible === true) {
				itemDiv.addClass('border-left-ppm-' + component.perf_color);
				// add any flags
    			// adding recommended to all for now
    			if (component.recommended === true ) {
    				//recommendedLabel.show(); // don't show for now
    			}
				// make item clickable (equippable)
				itemDiv.addClass('equippable-item');
			} else {        				
				itemDiv.addClass('border-left-ppm-gray');

				// item cannot be equipped
				itemDiv.removeClass('equippable-item');
			}
			
			/// if this item is equipped show it at the top
			if (currentEquippedId === component.id) itemListView.prepend(itemDiv);
			else itemListView.append(itemDiv);
			
    	}
	}
	
	//
	//
	// on equippable click event handle both the chart and list view
	function equippableItemClicked(componentId){
		// remove equip styling from all components
		
		var listItem = $('.equippable-item').filter('[data-component-id="' + componentId + '"]');
		
		$('.equip-part-item').find('.ppm-label-equipped').hide();
		listItem.find('.ppm-label-equipped').show();
		
		toEquip = componentId;
		console.log('the data: ' + toEquip);
		
		
		// if toEquip is null
		if (toEquip !== null) {
			// set edited part
			var currEquipId = currentRig['parts'][equipType + '_id'];
			if (currEquipId !== toEquip) currentRig['edited'][equipType] = true; // edited part
			
			// set part to equip in view
			console.log('equip ' + equipType + ' ' + toEquip);
			currentRig['parts'][equipType + '_id'] = toEquip;	
		}
		
		$('#part-item-list').slideUp(500);
		$('#pick-part-modal').modal('hide');
		renderRig();
		
		
	}
	
	//
	// Equip Part Item onClick
	// Change styling
	//
	function bindEquipListener(){
		$('.equippable-item').click(function(){
			equippableItemClicked($(this).data('component-id'));
		});
	}
	
	//
	// Format price from int representation
	//
	function formatPriceFromInt(intPriceVal) {
		intPriceVal = parseInt(intPriceVal);
		var dollars = parseInt(intPriceVal / 100);
		var cents = intPriceVal % 100;
		cents = (cents < 10) ? ("0" + cents) : cents;
		return String(dollars) + '.' + String(cents);
	}
	
	
	//
	// Render Bench View
	//
	function renderRig() {
		console.log('Rendering Rig');
		console.log(currentRig);
		
		// reset to fresh UI
		resetBenchUI();
		
		$('#expected-performance-section').hide();
		
		//
		//
		// Disable save and share button (assume cube positions have not all been filled)
		$('#save-my-cube-button').prop('disabled', true);
		$('#benchtab-share').addClass('benchtab-disabled');
		
		var coreComponentCount = 0;
		var worstComponent = null;
		var worstComponentDetail = null;
		var totalCostRaw = 0;
		
		// render the current rig
		for (comp in currentRig['parts']) {
			
			var compId = currentRig['parts'][comp];
			if (compId === null || compId === undefined) {
				continue;
			}
			
			// pull part and information from cache
			var partDetail = partsCache[compId];
			
			// comptype
			var compType = comp.substr(0, comp.indexOf('_id'));
			
			// modify view
			if (isCoreComponent(compType)) {
				// modify core view
				renderCoreComponent(compType, partDetail);
				
				//
				// incremenent component count
				// and set worst component
				coreComponentCount++;
				if (worstComponent == null || partDetail.perf_color_coded < worstComponent) {
						worstComponent = partDetail.perf_color_coded;
						worstComponentDetail = partDetail;
				}
			} else{
				// modify other view
				renderOtherComponent(compType, partDetail);
			}
			
			// add up total cost
			if (partDetail.priceraw) {
				totalCostRaw += partDetail.priceraw;
			}
			
		}
		
		if (totalCostRaw > 0) {
			$('.budget-total-cost').empty().text('$' + formatPriceFromInt(totalCostRaw));
			$('.no-prices-span').hide();
		} else {
			$('.budget-total-cost').empty();
			$('.no-prices-span').show();
		}
		
		if (coreComponentCount > 0) {
			// set center cube and avatar cubes
			$('#ac-cubedisplay-widget').attr('src','/static/cube-images/ac-cube-small-' + worstComponentDetail.perf_color + '.png');
			$('#bench-cube-title').addClass('border-' + worstComponentDetail.perf_color);
			$('#bench-cube-subtitle').html(constructPerformanceNote(worstComponentDetail)).removeClass().addClass('fg-' + worstComponentDetail.perf_color);
			
			
			$('#expected-performance-section').show();
			
			// enable save button and share button
			if (AC_GLOBALS.myRig) {
				$('#save-cube-button').text('Update Cube');
				$('#save-cube-button').show();
				if (currentRig && (Object.keys(currentRig['edited']).length > 0 || currentRig['miscEdited'] === true)) {
					$('#save-cube-button').attr('disabled', false);
				}
				else {
					$('#save-cube-button').attr('disabled', true);
				}
			} else if (blankRig) {
				$('#save-cube-button').text('Save Cube');
				$('#save-cube-button').show();
			}
			$('#benchtab-share').removeClass('benchtab-disabled');
			
			// enable equiping secondary components
			if (AC_GLOBALS.myRig || blankRig) {
				$('.other-clickable').click(renderPartPickerModal);
				$('.other-clickable').addClass('pointer');
			}
			$('.other-component-note').hide();
		} else {
			$('.other-clickable-btn').hide();
		}
		
		// set rig name
		if (currentRig.name !== undefined) {
			$('#bench-cube-title').html(currentRig['name']);
		}
		
		// render edited flags
		if (currentRig.rig_id !== undefined && currentRig.rig_id !==null){
			for (comp in currentRig['edited']) {
				renderEditedFlag(comp);
			}
		}
		$('.loading-spinner').hide();

		//
		//
		// determine genres to allow for genre toggle (based on cpu)
		var possibleGenres = [{name: 'First-person Shooter', key: 'FPS'},
		                     {name: 'Open World', key: 'OPEN_WORLD'}];
		genreSelector = [];
		if (currentRig.parts.cpu_id) {
			$('#resolution-selector').show();
			
			for (var i=0; i<possibleGenres.length; i++) {
				var fpsDataKey = 'fps_avg_' + possibleGenres[i].key;
				var cpuPart = partsCache[currentRig.parts.cpu_id];
				if (cpuPart[fpsDataKey]) {
					genreSelector.push({name : possibleGenres[i].name, selected : (i == 0), key : possibleGenres[i].key});
				}	
			}
			genreSelector[0].selected = true;
		}
		
		//
		//
		// determine and select resolutions
		selectedResolution = '1080p';
		possibleResolutions = {'1080p':true, '1440p': false, '2160p': false};
		if (currentRig.parts.gpu_id) {
			for (var i=0; i<possibleGenres.length; i++) {
				var gpuPart = partsCache[currentRig.parts.gpu_id];
				if (gpuPart['fps_1440p_' + possibleGenres[i].key]) possibleResolutions['1440p'] = true;
				if (gpuPart['fps_2160p_' + possibleGenres[i].key]) possibleResolutions['2160p'] = true;
				
				if (possibleResolutions['1440p'] && possibleResolutions['2160p']) break;
			}
		}
		
		//
		// finally render performance monitor
		renderPerformanceMonitor();
	}
	
	function toRigUseString(useEnum){
		if (useEnum === 'current') return "This is my current rig.";
		else if (useEnum === 'upgrade') return "This is an upgrade from your current rig.";
		else if (useEnum === 'fresh') return "This is a brand new rig.";
		else if (useEnum === 'recommend') return "I recommend this rig.";
		return null;
	}
	
	function renderCoreComponent(compType, partDetail){
		// modify core view
		var view = $('.ac-' + compType + '-section');
		view.prev().hide();// hide equip button
		view.empty();
		
		var displaySpan = $('<span></span>');
		displaySpan.append(constructDisplayName(partDetail));
		displaySpan.addClass('fg-' + partDetail.perf_color);
		displaySpan.addClass('part-item-title'); // styling

		view.append(displaySpan.clone());
		view.append('<br><span>' + constructPerformanceNote(partDetail) + '</span>')
		
		if (partDetail.priceformatted) {
			view.append('<br><span style="color:#0f9b3e;font-weight:bold;">' + partDetail.priceformatted + '</span>');
			$('.bench-buy-url').on('click', function(event){
			    event.stopPropagation();
			});
		}
		
		// modify colors
		$('.ac-cubedisplay-' + compType).attr('src',
				'/static/cube-images/ac-cube-small-' + partDetail.perf_color + '.png');
	}
	
	function renderOtherComponent(compType, partDetail){
		// modify core view
		var view = $('.ac-' + compType + '-section');
		view.prev().hide();// hide equip button
		view.empty();
		
		var displaySpan = $('<span></span>');
		displaySpan.append(constructDisplayName(partDetail));
		displaySpan.addClass('part-item-title'); // styling

		view.append(displaySpan.clone());
		if (partDetail.priceformatted) {
			view.append('<br><span style="color:#0f9b3e;font-weight:bold;">' + partDetail.priceformatted + '</span>');
			$('.bench-buy-url').on('click', function(event){
			    event.stopPropagation();
			});
		}
	}
	
	function renderEditedFlag(compType){
		// modify core view
		var view = $('.ac-' + compType + '-section');
		view.siblings('.label-edited').show();
	}
	
	function resetBenchUI(){
		//
		//
		// RESET Cube positions
		$('.ac-cubedisplay-middle').attr('src','/static/cube-images/ac-cube-middle-default.png');
		$('.ac-cubedisplay-gpu').attr('src','/static/cube-images/ac-cube-small-default.png');
		$('.ac-cubedisplay-cpu').attr('src','/static/cube-images/ac-cube-small-default.png');
		$('.ac-cubedisplay-memory').attr('src','/static/cube-images/ac-cube-small-default.png');
		$('.ac-cubedisplay-display').attr('src','/static/cube-images/ac-cube-small-default.png');
		$('#bench-cube-title').removeClass();
		$('#bench-cube-subtitle').empty();
		$('#bench-upgrade-subtitle').empty();
		$('#bench-rig-use-subtitle').empty();
		
		//
		//
		// Remove display titles
		$('.item-slot-section').empty();
		
		//
		//
		// show all equip buttons
		$('.equipbutton').show();
		$('.other-clickable-btn').show();
		
		//
		//
		// Other components cannot be edited by default (assuming cube not filled)
		$('.other-clickable').removeClass('pointer');
		$('.other-clickable').unbind();
		$('.other-component-note').show();
		
		//
		//
		// Do not show save cube button
		$('#save-cube-button').hide();
		
		//
		// Hide all edited labels
		$('.label-edited').hide();
		
		$('#resolution-selector').hide();
	}
	
	function constructDisplayName(part){
		var partName = "";
		if (part.display_name !== null && part.display_name !== undefined && part.display_name !== '') return part.display_name;
		if (part.vendor !== undefined && part.vendor !== null) partName += part.vendor + ' ';
		if (part.brand_name !== undefined && part.brand_name !== null) partName += part.brand_name + ' ';
		if (part.model_number !== undefined && part.model_number !== null) partName += part.model_number;
		return partName;
	}
	
	function constructPerformanceNote(part){
		var note = "";
		if (part.max_performance !== undefined && part.max_performance !== null) note += part.max_performance + ' ';
		if (part.resolution !== undefined && part.resolution !== null) note += part.resolution;
		if (part.max_framerate !== undefined && part.max_framerate !== null) note += '<br>' + part.max_framerate + ' Hz Refresh Rate';
		return note;
	}
	
	function isCoreComponent(compType) {
		//return compType === 'memory' || compType === 'display' || compType === 'cpu' || compType === 'gpu';
		// modified for widget
		return compType === 'cpu' || compType === 'gpu';
	}
	
	function refreshPartsCache(renderFunc){
		// retrieve necessary parts from server
		var ids = '';
		var count = 0;
		for (part in currentRig['parts']) {
			count++;
			if (currentRig['parts'][part] === null) continue;
			
			ids += currentRig['parts'][part];
			if (count < Object.keys(currentRig.parts).length) {
				ids += ',';
			}
		}
		if (ids.length === 0) renderFunc();
		$.getJSON( "/widgetgetparts", {ids:ids}).success(function(data) {
			var partsList = data;
        	for (part in partsList) {
        		var component = partsList[part];
        		partsCache[component.id] = component;
        	}
        	
        	if (renderFunc !== null) {
        		renderFunc();
        	}
		});
	}
	
	$('#change-cube-select').change(function(){
		window.location.href = $(this).find(":selected").data('location');
	});

	$('#show-cube-summary').click(function(){
		$('#build-cube-div').show();
		$('#other-components-bg').show();
		$('#share-cube-div').hide();
	});

	$('#show-share-cube').click(function(){
		$('#share-cube-div').show();
		$('#build-cube-div').hide();
		$('#owned-parts-div').hide();
	});
	
	$('#back-to-cube-btn').click(function(){
		$('#share-cube-div').hide();
		$('#build-cube-div').show();
		$('#owned-parts-div').show();
	});

	$('#twitter-share-btn').attr('href', 'https://twitter.com/share?url=' + window.location.href);

	$('#facebook-share-btn').attr('href', 'https://www.facebook.com/sharer.php?u=' + window.location.href);

	$('#reddit-share-btn').attr('href', 'http://www.reddit.com/submit?url=' + window.location.href);

	$('#get-share-link-btn').click(function(){
		$('#share-link-input').val(window.location.href);
		$('#share-link-div').show();
	});

	$('#copy-share-link-btn').click(function(){
		$('#share-link-input').val($('#share-link-input').val()).select();
		document.execCommand("copy");
	});
	
	$('#legendIconButton').click(function(){
		// open legend modal
		$('#legend-modal').modal('show');
		
	});
	
	$('.rig-type-selector').click(function(){
		
		$('.continue-save-btn').prop( "disabled", false );
		
		// select one
		var rigSelect = $(this).find('.select-rig-type');
		var selectUrl = $(this).data('selected-img');
		var rigType = $(this).data('type');
		currentRig['owned'] = rigType === 'owned';
		rigSelect.addClass('selected-rig-type').removeClass('select-rig-type').find('img').attr('src', selectUrl);
		
		
		// deselect the other one
		var otherSelector = $(this).siblings('.rig-type-selector'); 
		var rigDeselect = otherSelector.find('.selected-rig-type');
		var deselectUrl = otherSelector.data('deselect-img');
		rigDeselect.addClass('select-rig-type').removeClass('selected-rig-type').find('img').attr('src', deselectUrl);
		
	});
	
	//
	//
	//
	//
	//
	// ///////////////////////////////////////////
	//
	// Performance meter
	//
	// ///////////////////////////////////////////
	//
	//
	
	var genreSelector = null;
	var selectedResolution = '1080p';
	var possibleResolutions = {'1080p':true, '1440p': false, '2160p': false};
	
	$('.resolution-select-btn').click(function(){
		selectedResolution = $(this).data('resolution');
		$('.resolution-select-btn').removeClass('active');
		$(this).addClass('active');
		renderPerformanceMonitor();
	});
	
	function renderPerformanceMonitor() {
		
		//
		// modify selected resolution button
		$('.resolution-select-btn').removeClass('active');
		$('.resolution-select-btn[data-resolution="' + selectedResolution + '"]').addClass('active');
		
		//
		// disable resolution buttons if they are not possible
		for (theKey in possibleResolutions) {
			if (possibleResolutions[theKey]) $('.resolution-select-btn[data-resolution="' + theKey + '"]').removeAttr('disabled', 'disabled');
			else  $('.resolution-select-btn[data-resolution="' + theKey + '"]').attr('disabled', 'disabled');
		}
		
		$('.performance-meter-holder').hide();
		
		$('.performance-meter-container').hide();
		if (genreSelector.length > 0) $('.performance-meter-container').show();
		
		for (var i = 0; i < genreSelector.length; i++) {
			
			var currGenre = genreSelector[i];
			
			var cpuPart = partsCache[currentRig.parts.cpu_id];
			if (currentRig.parts.gpu_id) {
				var gpuPart = partsCache[currentRig.parts.gpu_id];
				
				renderHealthBar(gpuPart['fps_' + selectedResolution + '_' + currGenre.key], cpuPart['fps_avg_' + currGenre.key], currGenre.key, currGenre);
			} else {
				renderHealthBar(null, cpuPart['fps_avg_' + currGenre.key], currGenre.key, currGenre);
			}
		}
		
		// render chart
		if (currentRig.parts.cpu_id && currentRig.parts.gpu_id) {
			$.getJSON( "/fpstable", { cpu_id: currentRig.parts.cpu_id, gpu_id: currentRig.parts.gpu_id} , function( data ) {
				var fpsTable = constructFpsTable(data);
				$('#resource-monitor-fps-table').empty();
				$('#resource-monitor-fps-table').append(fpsTable);
			});
		} else{
			$('#resource-monitor-fps-table').empty();
			$('#resource-monitor-fps-table').append('<h5>Please select a Processor and a Graphics Card</h5>');
		}
		
	}
	
	function renderHealthBar(gpuFps, cpuFps, genreKey, currGenre){
		
		var meterContainer = $('#' + genreKey + '_METER');
		var healthBar = meterContainer.find('.health-bar');
		var healthMeter = meterContainer.find('.health-meter');
		
		healthBar.hide();
		healthMeter.hide();
		
		if (!cpuFps) {
			meterContainer.hide();
			return;
		}
		
		var healthBarSize = parseInt((cpuFps/200)*100) + '%';
		healthBar.css('width', healthBarSize);
		healthBar.show();
		var healthBarWidth = healthBar.add(':visible').width();
		
		if (gpuFps) {
			var healthMeterSize = null;
			if (gpuFps >= cpuFps) {
				healthMeterSize = '100%';
			} else {
				healthMeterSize = parseInt((gpuFps/cpuFps) * 100) + '%';
			}
			
			healthMeter.show();
			
			healthMeter.animate({width:healthMeterSize}, 500, function(){
				var healthMeterWidth = gpuFps > cpuFps ? healthBarWidth : healthMeter.add(':visible').width();
			});
		} else{
			healthMeter.css('width', '');
		}
		
		// show it then
		meterContainer.show();
	}
	
	
	
});