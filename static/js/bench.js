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
	} else if (AC_GLOBALS.cpu !== null || AC_GLOBALS.gpu !== null) {
        populateRigWithPreselected(AC_GLOBALS.cpu, AC_GLOBALS.gpu);
    } else if (AC_GLOBALS.rig !== null) {
		populateRigById(AC_GLOBALS.rig);
		currentRig['rig_id'] = AC_GLOBALS.rig; // set ID for subsequent saves to update
	}
	else {
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
	
	
	function populateRigWithPreselected(preselectedCpu, preselectedGpu) {
	    if (preselectedCpu) currentRig['parts']['cpu_id'] = parseInt(preselectedCpu);
	    if (preselectedGpu) currentRig['parts']['gpu_id'] = parseInt(preselectedGpu);
	    currentRig['miscEdited'] = true;
	    refreshPartsCache(renderRig);
	}
	
	function populateRigById(rigId){
		//
		//
		// GET RIG INFO, SET, AND RENDER
		$.getJSON( "/getrig", {rig_id: rigId}).success(function(data) {
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
            currentRig['miscEdited'] = true;
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
	
	function silentlySave(){
	    // very silently
	    if (AC_GLOBALS.anonRig) {
	        var postRig = Object.assign({}, currentRig['parts']);
	        postRig['name'] = currentRig['name'];
	        postRig['owned'] = currentRig['owned'] && currentRig['owned'] === true;
	        
	        $.post('/saveanon', postRig).success(function(data){
	            console.log('rig silently saved: '+ data.rig_id); 
	        });
        }
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
		$('#pick-part-modal').modal('hide');
		
		renderRig();
	});
	
	$('#modal-unequip-btn').click(function(){
		console.log('unequip ' + equipType);
		currentRig['parts'][equipType + '_id'] = null;
		$('#part-item-list').empty();
		$('#pick-part-modal').modal('hide');
		renderRig();
	});
	
	//
	// dismiss modal (cancel)
	//
	$('#modal-cancel-btn').click(function(){
		$('#part-item-list').empty();
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
		if (componentEType === 'cpu') {
			$('#cpu-chart-container').show();
		}
		else {
			$('#part-picker-tabs').hide();
			$('#cpu-chart-container').hide();
			$('#coming-soon-chart-container').show();
		}
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
        $.getJSON( "/getparts", getPartsParams).success(function(data) {
        	
        	renderFromPartsList(data, currentEquippedId);
        	
        	bindEquipListener();
        	
        	$('.ppm-loading-spinner').hide();
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
		
		$('#pick-part-modal').modal('show');
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
			var fpsTable = constructFpsTable(component.fps_data_table);
			contentLeft.append(fpsTable);
		}
		
		// content on right
		var contentRight = $('<div class="col-xs-4 col-md-2"></div>');
		if (component.priceformatted) {
			contentRight.append('<span class="part-item-price">' + component.priceformatted + '</span><br><small>On Amazon</small>');
		} else {
			contentRight.append('<span class="part-item-unavailable">Component not available</span>');
		}
		var labels = $('<br><br><span class="label ppm-label ppm-label-equipped">EQUIPPED</span><br><br><span class="label ppm-label ppm-label-recommended">RECOMMENDED</span>&nbsp;&nbsp;&nbsp;&nbsp;</div>');
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
    				recommendedLabel.show();
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
				if (isCoreComponent(compType)) {
					coreComponentCount++;
					if (worstComponent == null || partDetail.perf_color_coded < worstComponent) {
							worstComponent = partDetail.perf_color_coded;
							worstComponentDetail = partDetail;
					}
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
		
		if (coreComponentCount == 4) {
			// set center cube and avatar cubes
			$('#ac-cubedisplay-middle').attr('src','/static/cube-images/ac-cube-middle-' + worstComponentDetail.perf_color + '.png');
			$('#bench-cube-title').addClass('border-' + worstComponentDetail.perf_color);
			$('#bench-cube-subtitle').html(constructPerformanceNote(worstComponentDetail));
			
			// enable save button and share button
			if (AC_GLOBALS.myRig) {
				$('#save-cube-button').text(AC_GLOBALS.anonRig ? 'Save Cube' : 'Update Cube');
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
		if (currentRig.rig_id !== undefined && currentRig.rig_id !==null && !AC_GLOBALS.anonRig){
			for (comp in currentRig['edited']) {
				renderEditedFlag(comp);
			}
		}
		$('.loading-spinner').hide();

		// determine genres to allow for genre toggle (based on cpu)
		var possibleGenres = [{name: 'First-person Shooter', key: 'FPS'},
		                     {name: 'Open World', key: 'OPEN_WORLD'},
		                     {name: 'PlayerUnknown\'s Battlegrounds', selected:false, key: 'PUBG'}];
		genreSelector = [];
		if (currentRig.parts.cpu_id) {
			for (var i=0; i<possibleGenres.length; i++) {
				var fpsDataKey = 'fps_avg_' + possibleGenres[i].key;
				var cpuPart = partsCache[currentRig.parts.cpu_id];
				if (cpuPart[fpsDataKey]) {
					genreSelector.push({name : possibleGenres[i].name, selected : (i == 0), key : possibleGenres[i].key});
				}	
			}
			if (genreSelector.length > 0) {
				genreSelector[0].selected = true;
				selectedGenre = genreSelector[0];	
			}
		}
		renderPerformanceMonitor();
		
	    //
        // do a silent save if needed
        silentlySave();
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
			view.append('<br><span style="color:#0f9b3e;font-weight:bold;">' + partDetail.priceformatted + '</span> <a class="bench-buy-url" target="_blank" href="'+partDetail.buyurl+'">Buy on Amazon</a>');
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
			view.append('<br><span style="color:#0f9b3e;font-weight:bold;">' + partDetail.priceformatted + '</span> <a class="bench-buy-url" target="_blank" href="'+partDetail.buyurl+'">Buy on Amazon</a>');
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
		return compType === 'memory' || compType === 'display' || compType === 'cpu' || compType === 'gpu';
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
		$.getJSON( "/getparts", {ids:ids}).success(function(data) {
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
	var selectedGenre = null;
	
	var resolutionSelector = [{name: '1080p', selected:true, key: '1080p'},
	 	                      {name: '1440p', selected:false, key: '1440p'},
	 	                      {name: '2160p', selected:false, key: '2160p'}];
	var selectedResolution = resolutionSelector[0];
	
	function moveToNextSelection(optionsArray) {
		var nextIndex = 0;
		var noneSelected = true;
		for (var i=0; i < optionsArray.length; i++) {
			if (optionsArray[i].selected) {
				
				if (optionsArray.length === 1) return optionsArray[i];
				
				optionsArray[i].selected = false;
				if (i < optionsArray.length - 1 ) nextIndex = i + 1;
				noneSelected = false;
				break;
			}
		}
		
		if (noneSelected) {
			return null;
		} else {
			optionsArray[nextIndex].selected = true;
			return optionsArray[nextIndex];
		}
		
	}
	
	$('.health-bar-genre-selector').click(function(){
		
		
		$('.health-bar-genre-selector').empty();
		selectedGenre = moveToNextSelection(genreSelector);
		if(selectedGenre) $('.health-bar-genre-selector').append(selectedGenre.name);
		
		renderPerformanceMonitor();
	});
	
	$('.health-bar-resolution-selector').click(function(){
		
		selectedResolution = moveToNextSelection(resolutionSelector);
		
		$('.health-bar-resolution-selector').empty();
		$('.health-bar-resolution-selector').append(selectedResolution.name);
		
		renderPerformanceMonitor();
	});
	
	var fullReportCardVisible = false;
	function toggleResourceMonitor(closeOnly){
		closeOnly = closeOnly || false;
		
		if (fullReportCardVisible) {
			//
			// close monitor
			$('.report-card-full-container').animate(
					{bottom:$('.report-card-preview-container').height() - $('.report-card-full-container').height()},
					300,
					function(){
						$('.report-card-full-container').hide();
						$('.report-card-preview-container').show();
						fullReportCardVisible = false;
					});
			
		} else if (!closeOnly) {
			//
			// opens monitor
			$('.report-card-full-container').css('bottom', $('.report-card-preview-container').height() - $('.report-card-full-container').height());
			$('.report-card-preview-container').hide();
			$('.report-card-full-container').show();
			$('.report-card-full-container').animate({bottom: 0}, 300);
			fullReportCardVisible = true;
		}
	}
	
	// toggle if toggle button clicked
	$('.report-card-toggle').click(function(){
		toggleResourceMonitor();
	});
	
	// don't propagate clicks
	$('.report-card-full-container, .report-card-preview-container').click(function(e){
		e.stopPropagation();
	});
	
	function renderPerformanceMonitor() {
		// render based on rig information
		if (currentRig.parts.cpu_id && selectedGenre) {
			
			// get CPU fps
			var cpuPart = partsCache[currentRig.parts.cpu_id];
			if (currentRig.parts.gpu_id) {
				var gpuPart = partsCache[currentRig.parts.gpu_id];
				
				renderHealthBar(gpuPart['fps_' + selectedResolution.key + '_' + selectedGenre.key], cpuPart['fps_avg_' + selectedGenre.key]);
			} else {
				renderHealthBar(null, cpuPart['fps_avg_' + selectedGenre.key]);
			}
			
		} else {
			renderHealthBar(null, null);
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
	
	function renderHealthBar(gpuFps, cpuFps){
		
		if (selectedGenre) {
			$('.health-bar-genre-selector').empty();
			$('.health-bar-genre-selector').append(selectedGenre.name);
		}
		
		$('.report-card-toggle').hide();
		$('.health-bar').hide();
		$('.health-meter').hide();
		$('.cpu-meter-readout').empty();
		$('.gpu-meter-readout').empty();
		
		if (!cpuFps) {
			$('.performance-meter-container').hide();
			return;
		}
		
		$('.report-card-toggle').show();
		
		$('.performance-meter-container').show();
		
		var healthBarSize = parseInt((cpuFps/200)*100) + '%';
		$('.health-bar').css('width', healthBarSize);
		$('.health-bar').show();
		$('.cpu-meter-readout').append(cpuFps + ' FPS<br>(Processor)');
		var healthBarWidth = $('.health-bar:visible').width();
		$('.cpu-meter-readout').css('left', healthBarWidth - 10 + 'px');
		
		if (gpuFps) {
			var healthMeterSize = null;
			if (gpuFps >= cpuFps) {
				healthMeterSize = '100%';
			} else {
				healthMeterSize = parseInt((gpuFps/cpuFps) * 100) + '%';
			}
			$('.health-meter').text('');
			$('.health-meter').show();
			$('.gpu-meter-readout').append(gpuFps + (gpuFps > cpuFps ? ' FPS<br>(Graphics)<br>Limited by Processor!' : ' FPS<br>(Graphics)'));
			$('.gpu-meter-readout').css('color', '#0e0d18');
			$('.health-meter').animate({width:healthMeterSize}, 500, function(){
				var healthMeterWidth = gpuFps > cpuFps ? healthBarWidth : $('.health-meter:visible').width();
				$('.gpu-meter-readout').css('left', healthMeterWidth - 10 + 'px');
				$('.gpu-meter-readout').css('color', 'white');
			});
		} else{
			$('.health-meter').css('width', '');
			$('.health-meter').text('Select a GPU');
		}
	}
	
	//
	//
	//
	//
	//
	// ////////////////////////
	//
	// CHARTS
	//
	// ////////////////////////
	//
	//
	//
	//
	//
	//

	function currentEquippedDatapoint(allDataPoints) {
		var currEquippedId = toEquip ? toEquip : currentRig['parts']['cpu_id'];
		
		if (!currEquippedId) return null;
		
		for(var i=0;i<allDataPoints.length;i++) {
			// defnitely better way to do this i.e. store in map
			if(allDataPoints[i].component_id === currEquippedId) return allDataPoints[i];
		}
		
		return null;
	}
	
	function contructComponentPerformanceDiffSpan(dataPoint, prevDataPoint) {
		
		var avgFps = '';
		if (dataPoint.fps_average > prevDataPoint.fps_average) {
			avgFps += '<b style="color:green;">(+' + (dataPoint.fps_average - prevDataPoint.fps_average).toFixed(1) + ')</b>';
		} else if (dataPoint.fps_average !== prevDataPoint.fps_average) {
			avgFps += '<b style="color:red;">(-' + (prevDataPoint.fps_average - dataPoint.fps_average).toFixed(1) + ')</b>';
		}
		
		var oneFps = '';
		if (dataPoint.fps_one > prevDataPoint.fps_one) {
			oneFps += '<b style="color:green;">(+' + (dataPoint.fps_one - prevDataPoint.fps_one).toFixed(1) + ')</b>';
		} else if (dataPoint.fps_one !== prevDataPoint.fps_one) {
			oneFps += '<b style="color:red;">(-' + (prevDataPoint.fps_one - dataPoint.fps_one).toFixed(1) + ')</b>';
		}
		
		var msrp = '';
		if (dataPoint.msrp < prevDataPoint.msrp) {
			msrp += '<b style="color:green;">(-$' + (prevDataPoint.msrp - dataPoint.msrp ).toFixed(2) + ')</b>';
		} else if (dataPoint.fps_one !== prevDataPoint.fps_one) {
			msrp += '<b style="color:red;">(+$' + (dataPoint.msrp - prevDataPoint.msrp).toFixed(2) + ')</b>';
		}
		
		return {
			avgFps:avgFps,
			oneFps:oneFps,
			msrp:msrp
		};
		 
	}
	
	function constructComponentForTtHtml(dataPoint, addClassStr, plottedPoints) {
		var compatiblePart = partsCache[dataPoint.component_id] && partsCache[dataPoint.component_id].compatible;
		var classes = (addClassStr ? addClassStr : '') + ' ' + (compatiblePart ? 'clickable clickable-chart-part' : '');
		
		var compHtml = '<div class="chart-part-list-item ' + classes + '"  data-component-id="' + dataPoint.component_id + '">';
		
		var currentEquippedDp = currentEquippedDatapoint(plottedPoints);
		var componentIsEquipped = (currentEquippedDp && dataPoint.component_id === currentEquippedDp.component_id);
		var diffSpans = currentEquippedDp ? contructComponentPerformanceDiffSpan(dataPoint, currentEquippedDp) : null;
		
		compHtml += '<b class="' + 'fg-' + dataPoint.perf_color + '">'
		+ dataPoint.component_display_name + '</b>';
		compHtml += componentIsEquipped ? '&nbsp;&nbsp;<span class="label label-default">Equipped</span>' : '';
		compHtml += compatiblePart ? '' : '&nbsp;&nbsp;<span class="label label-danger">Incompatible</span>';
		compHtml += '<br><b>MSRP: </b> $' + dataPoint.msrp;
		compHtml += (diffSpans ? ' ' + diffSpans.msrp : '');
		compHtml += '<br><b>Average Framerate:</b> ' + dataPoint.fps_average;
		compHtml += (diffSpans ? ' ' + diffSpans.avgFps : '') + ' fps';
		compHtml += '<br><b>99th percentile:</b> ' + dataPoint.fps_one;
		compHtml += (diffSpans ? ' ' + diffSpans.oneFps : '') + ' fps';
		compHtml += '<br><b>Benchmark:</b> ' + dataPoint.benchmark_name;
		compHtml += (dataPoint.source_url && dataPoint.source_description) ? '<br><b>Source:</b> <a target="_blank" href="' + dataPoint.source_url + '">' + dataPoint.source_description + '</a>' : '';
		
		compHtml += '</div>';
		return compHtml;
	}
	
	function constructTooltipDiv(divName, dataPoint, shapePosition, plottedPoints) {
		
		var otherPartsHtml = '<div id="tt-others"><hr><h5>Other parts in same price range:</h5>';
		var otherPartsExist = false;
		for (var i = 0; i < dataPoint.others.length; i++) {
			var otherComp = dataPoint.others[i];
			otherPartsHtml += constructComponentForTtHtml(otherComp, 'hover-other-part', plottedPoints);
			otherPartsExist = true;
		}
		otherPartsHtml += '</div>';
		
		var ttHtml = '<div id="' + divName + '" class="chart-tt remove-click-away">';
		ttHtml += '<div class="text-center" id="select-part-chart-title" style="display:none"><br><span class="text-center small">Select Part to Equip</span></div>';
		ttHtml += '<div class="chart-tt-internal">';
		ttHtml += constructComponentForTtHtml(dataPoint, '', plottedPoints);
		ttHtml += '<div style="display:none" id="tt-equip-div">';
		ttHtml += (otherPartsExist ? otherPartsHtml : '');
		ttHtml += '</div>';
		ttHtml += '</div>'; // END chart-tt-internal div
		ttHtml += '</div>'; // END chart-tt div
		
		var tt = $(ttHtml);
		var shapeGap = 45; // by default render tt about 50px away from shape
		
		// increase gap if the chart is very zoomed in
		var currentLayout = document.getElementById('cpu-chart-tab').layout;
		if (currentLayout && currentLayout.xaxis.range) {
			var startRange = currentLayout.xaxis.range[0];
			var endRange =  currentLayout.xaxis.range[1];
			if ((endRange - startRange) < 100) shapeGap = 85;
			if ((endRange - startRange) < 50) shapeGap = 150;
		}
		
		// determine vertical position based on window size
		var preferredVertical = (shapePosition.top - 150);
		if ((preferredVertical + 330) > window.innerHeight) preferredVertical = preferredVertical - ((preferredVertical + 330) - window.innerHeight);
		tt.css('top', preferredVertical + 'px');
		
		// determine left or right side
		var renderToRight = (window.innerWidth - shapePosition.left) > 380;
		if (renderToRight) tt.css('left', (shapePosition.left + shapeGap) + 'px');
		else tt.css('left', (shapePosition.left - shapeGap - 380) + 'px');
		
		return tt;
	}
	
	function createShape(dp, outlineColor) {
		if (dp.svg_plot === null || dp.svg_plot === undefined || dp.svg_plot === "") return null;
		return {
			type : 'path',
			path : dp.svg_plot,
			fillcolor: dp.background_rgba,
		    line: {
		    	color: outlineColor ? outlineColor : dp.outline_rgb
		    }
		};
	}
	
	function generateShapes(dataPoints, otherComponent) {
		var shapes = [];
		var otherRendered = false;
		for (var i = 0; i < dataPoints.length; i++) {
			
			var dp = dataPoints[i];
			
			var outlineColor = null;
			if (toEquip && toEquip === dp.component_id) {
				outlineColor = 'rgb(255,255,255)';
			}
			else if (dp.component_id === currentRig['parts']['cpu_id'] && !toEquip) {
				outlineColor = 'rgb(255,255,255)';
			}
			
			var shape = createShape(dp, outlineColor);
			if (shape) shapes.push(shape);
			else continue;
			
			if (otherComponent && !otherRendered) {
				// iterate through other components:
				for (var j = 0; j < dp.others.length; j++) {
					var otherDp = dp.others[j];
					if (otherDp.component_id == otherComponent) {
						// render shape
						var shape = createShape(otherDp, null);
						if (shape) shapes.push(shape);
						otherRendered = true;
						break;
					}
				}
			}
		}
		return shapes;
	}
	
	function generateChartData(dataPoints) {
		var plottedPoints = [];
		var trace1 = {
			  x: [],
			  y: [],
			  text: [],
			  mode: 'none',
			  hoverinfo: 'none'
			};
		
		// create trace
		for (var i = 0; i < dataPoints.length; i++) {
			var dp = dataPoints[i];
			trace1.x.push('$' + dp.msrp);
			trace1.y.push(dp.fps_average - ((dp.fps_average - dp.fps_one)/4));
			trace1.text.push(dp.component_display_name);
			plottedPoints.push(dp);
		}
		
		// create shapes
		var shapes = generateShapes(dataPoints, null);
		
		var layout = {
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
				  gridcolor: "#333333",
				  range: [0,200],
				  fixedrange : true
			  },
			  margin: {
				  l:50,r:70,t:10,b:50,pad:15
			  },
			  width: 900,
			  height: 400,
			  shapes: shapes,
			  hovermode: "closest",
			  paper_bgcolor: 'rgba(0,0,0,0)',
			  plot_bgcolor: 'rgba(0,0,0,0)',
			  font : {
				  color:"#aaaaaa"
			  }
		};
		return {
			plottedPoints: plottedPoints,
			trace1: trace1,
			layout: layout
		};
	}
	
	function determinePointsToPlot(allDataPoints) {
		var dpsToPlot = [];
		for (var i = 0; i < allDataPoints.length; i++) {
			var dp = allDataPoints[i];
			
			if ((toEquip && toEquip === dp.component_id) || (dp.component_id === currentRig['parts']['cpu_id'] && !toEquip)) {
				// add to list and continue, no need to look at other dps
				dp.equipped = true;
				dpsToPlot.push(dp);
				continue;
			}
			
			// check if any child dps are currently equipped
			var childDpEquipped = null;
			for (var j = 0; j < dp.others.length; j++) {
				var childDp = dp.others[j];
				if ((toEquip && toEquip === childDp.component_id) || (childDp.component_id === currentRig['parts']['cpu_id'] && !toEquip)) {
					childDpEquipped = childDp;
					childDp.equipped = true;
					break;
				}
			}
			
			if (childDpEquipped) {
				// this is now the main dp, add others (including parent)
				var others = [];
				
				others.push(dp); // parent
				for (var j = 0; j < dp.others.length; j++) {
					// add others, not including equipped
					var otherDp = dp.others[j];
					if (otherDp.component_id === childDpEquipped.component_id) continue;
					others.push(otherDp);
				}
				
				childDpEquipped.others = others;
				dpsToPlot.push(childDpEquipped);
				
			} else {
				// otherwise simply add this dp to be plotted
				dpsToPlot.push(dp);
			}
		}
		return dpsToPlot;
		
	}
	
	var fpsData = null;
	function renderChart(genre, fpsDataIn, persistZoom){
		persistZoom = persistZoom || false;
		
		fpsData = fpsDataIn;
		var rawDataPoints = fpsData[genre] !== undefined ? fpsData[genre].datapoints : [];
		
		var dataPoints = determinePointsToPlot(rawDataPoints);
		
		var chartData = generateChartData(dataPoints);
		
		if (persistZoom) {
			// grab currently rendered layout
			var currentLayout = document.getElementById('cpu-chart-tab').layout;
			if (currentLayout) {
				chartData.layout.xaxis.range = currentLayout.xaxis.range;
			}
		}
		
		Plotly.newPlot('cpu-chart-tab', [chartData.trace1], chartData.layout, {displayModeBar: false});
		
		document.getElementById('cpu-chart-tab')
		.on('plotly_hover', function(data){
			
			if ($('#chart-tooltip-div').length) {
				// dialog is already visible do nothing
				return;
			}
			
			var dataIn = data;
			var pointNumber = data.points[0].pointNumber;		
			
			var path = $('#cpu-chart-tab').find('path[data-index="' + pointNumber + '"]');
			var position = path.position();
			
			var dp = chartData.plottedPoints[pointNumber];
			var tt = constructTooltipDiv('chart-tooltip-div', dp, position, chartData.plottedPoints);
			$('body').append(tt);
			
			chartData.layout.shapes[pointNumber].fillcolor = 'rgba(255, 15, 15, 0.5)';
			chartData.layout.shapes[pointNumber].line.color = 'rgb(255, 15, 15)';
			
			Plotly.plot('cpu-chart-tab', null, chartData.layout, {displayModeBar: false});
			
			document.getElementsByClassName('nsewdrag')[0].style.cursor = 'pointer';
			
			
		})
		.on('plotly_unhover', function(data){
			var dataIn = data;
			var pointNumber = data.points[0].pointNumber;
			var dataPoint = chartData.plottedPoints[pointNumber];
			
			// render shapes (in case there are changes)
			chartData.layout.shapes = generateShapes(dataPoints, null);
			
			if (!$('#chart-tooltip-div').hasClass('clicked')) {
				$('#chart-tooltip-div').remove();
			}
			
			Plotly.plot('cpu-chart-tab', null, chartData.layout, {displayModeBar: false});
			
			document.getElementsByClassName('nsewdrag')[0].style.cursor = '';
			
		})
		.on('plotly_click', function(data){
			$('#chart-tooltip-div').addClass('clicked');
			$('#tt-equip-div').show();
			$('#select-part-chart-title').show();
			
			// bind equip click event
			$('.clickable-chart-part').click(function(){
				equippableItemClicked($(this).data('component-id'));
				$('#chart-tooltip-div').remove();
				
				// re-render the whole chart
				renderChart(genre, fpsData, true);
			});
			
			// bind mouse over and mouse out for other parts
			$('.hover-other-part').mouseover(function(){
				chartData.layout.shapes = generateShapes(dataPoints, $(this).data('component-id'));
				Plotly.plot('cpu-chart-tab', null, chartData.layout, {displayModeBar: false});
			}).mouseout(function(){
				chartData.layout.shapes = generateShapes(dataPoints, null);
				Plotly.plot('cpu-chart-tab', null, chartData.layout, {displayModeBar: false});
			});
			
			$('#tt-close-button').click(function(){
				$('#chart-tooltip-div').remove();
			});
			
			// ensure this tooltip stays visible if it's clicked on
			$('.remove-click-away').click(function(e){
				e.stopPropagation();
			});
		});
	}
	
	// change on genre being selected
	$('.genre-select-btn').click(function(){
		var genre = $(this).data('genre');
		$('.genre-select-btn').removeClass('active');
		$(this).addClass('active');
		renderChart(genre, fpsData); // for now just pass in previously pulled data
	});
	
	//
	// when tab is selected kick off render again, also select genre
	$('#chart-tab-selector').click(function(){
		var genre = $('.genre-select-btn[class*="active"]').data('genre');
		renderChart(genre, fpsData);
	});
	
	//
	//
	// pull component FPS data when page loads (for now)
	// NOTE: this is done on page load!
	$.getJSON( "/componentfps", function( data ) {
		// initially render FPS chart
		renderChart('FPS', data.fps_data);
	});
	
	//
	// remove any tooltip with class when it's not clicked on (or in)
	$(document).click(function(){
		$('.remove-click-away').remove();
		toggleResourceMonitor(true);
	});
	
});