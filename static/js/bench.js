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
					var text = $('#ac-' + comp + '-section').find('.part-item-title').text();
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
	$('#search-parts-input').keyup(function(){ searchPartsAndRenderResult(); });
	$('#search-show-only-compat-parts').change(function(){ searchPartsAndRenderResult(); });
	$('#search-rank-select').change(function(){ searchPartsAndRenderResult(); });
	$('#search-manufacturer-select').change(function(){ searchPartsAndRenderResult(); });

	function searchPartsAndRenderResult() {
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

        }).fail(function() {
            console.log( "error" );
        });
	}
	
	//
	// Rendering PART PICKER MODAL
	//
	function renderPartPickerModal() {
		var eType = $(this).parent().data('equip-type');
		equipType = eType;
		
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
        $.getJSON( "getparts", getPartsParams).success(function(data) {
        	
        	renderFromPartsList(data, currentEquippedId);
        	
        	bindEquipListener();

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

	function renderFromPartsList(data, currentEquippedId) {
		var itemListView = $('#part-item-list');
    	itemListView.empty();
    	
		var partsList = JSON.parse(data.parts);
    	for (part in partsList) {	        		
    		var component = partsList[part];
    		
    		//
    		// add to parts cache (needed later)
    		partsCache[component.id] = component;
    		
			var itemDiv = $('<div class="equip-part-item"></div>')
			var contentDiv = $('<div class="part-item-content"></div>')
			var iconDiv = $('<div class="part-icon-div"></div>')
			var titleSpan = $('<span class="part-item-title">' + constructDisplayName(component) + '</span>');
			
			itemDiv.append(iconDiv);
			itemDiv.append(contentDiv);
			contentDiv.append(titleSpan);
			
			//
			// set component ID
			//
			itemDiv.attr('data-component-id', component.id);
			
			// style current equipped if exists
			if (currentEquippedId === component.id) {
				itemDiv.addClass('equipped');
			} else {
				itemDiv.addClass("not-equipped");
			}
			
			if (component.compatible === true) {
				iconDiv.append('<img class="modal-color-icon" src="/static/images/modal-box-rarity-'+component.perf_color+'.png"/>') 	// color icon
				titleSpan.addClass('fg-' + component.perf_color);											// style title span
				contentDiv.append('<span class="part-item-sub">' + constructPerformanceNote(component) + '</span>');
				
				// add any flags
    			// adding recommended to all for now
    			if (component.recommended === true ) {
    				itemDiv.addClass('recommended-item');
    			}
				
				// make item clickable (equippable)
				itemDiv.addClass('equippable-item');
				
			} else {        				
				iconDiv.append('<img class="modal-color-icon" src="/static/images/modal-box-rarity-incompatible.png"/>') 	// append incompat icon
				contentDiv.append('<span class="part-item-sub fg-inc-red">INCOMPATIBLE</span>'); 			// incompatible text
				titleSpan.addClass('fg-inc'); 															// title color
				
				// item cannot be equipped
				itemDiv.removeClass('equippable-item');
			}
			
			itemListView.append(itemDiv);
			
    	}
	}
	
	//
	//
	// on equippable click event handle both the chart and list view
	function equippableItemClicked(componentId){
		// remove equip styling from all components
		
		var listItem = $('.equippable-item').filter('[data-component-id="' + componentId + '"]');
		console.log('got list item: ');
		console.log(listItem);
		
		$('.equip-part-item').removeClass('equipped');
		listItem.addClass('equipped');
		listItem.removeClass('not-equipped');
		
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
			console.log('comp type: ' + compType);
			
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
			
		}
		
		if (coreComponentCount == 4) {
			// set center cube and avatar cubes
			$('#ac-cubedisplay-middle').attr('src','/static/cube-images/ac-cube-middle-' + worstComponentDetail.perf_color + '.png');
			$('#bench-cube-title').addClass('border-' + worstComponentDetail.perf_color);
			$('#bench-cube-subtitle').html(constructPerformanceNote(worstComponentDetail));
			
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
		var view = $('#ac-' + compType + '-section');
		view.prev().hide();// hide equip button
		view.empty();
		
		var displaySpan = $('<span></span>');
		displaySpan.append(constructDisplayName(partDetail));
		displaySpan.addClass('fg-' + partDetail.perf_color);
		displaySpan.addClass('part-item-title'); // styling

		view.append(displaySpan.clone());
		view.append('<br><span>' + constructPerformanceNote(partDetail) + '</span>')
		
		// modify colors
		$('#ac-cubedisplay-' + compType).attr('src',
				'/static/cube-images/ac-cube-small-' + partDetail.perf_color + '.png');
	}
	
	function renderOtherComponent(compType, partDetail){
		// modify core view
		var view = $('#ac-' + compType + '-section');
		view.prev().hide();// hide equip button
		view.empty();
		
		var displaySpan = $('<span></span>');
		displaySpan.append(constructDisplayName(partDetail));
		displaySpan.addClass('part-item-title'); // styling

		view.append(displaySpan.clone());
		
	}
	
	function renderEditedFlag(compType){
		// modify core view
		var view = $('#ac-' + compType + '-section');
		view.siblings('.label-edited').show();
	}
	
	function resetBenchUI(){
		//
		//
		// RESET Cube positions
		$('#ac-cubedisplay-middle').attr('src','/static/cube-images/ac-cube-middle-default.png');
		$('#ac-cubedisplay-gpu').attr('src','/static/cube-images/ac-cube-small-default.png');
		$('#ac-cubedisplay-cpu').attr('src','/static/cube-images/ac-cube-small-default.png');
		$('#ac-cubedisplay-memory').attr('src','/static/cube-images/ac-cube-small-default.png');
		$('#ac-cubedisplay-display').attr('src','/static/cube-images/ac-cube-small-default.png');
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
		$.getJSON( "getparts", {ids:ids}).success(function(data) {
			var partsList = JSON.parse(data.parts);
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
			avgFps += '<b style="color:green;">(+' + (dataPoint.fps_average - prevDataPoint.fps_average).toFixed(2) + ')</b>';
		} else if (dataPoint.fps_average !== prevDataPoint.fps_average) {
			avgFps += '<b style="color:red;">(-' + (prevDataPoint.fps_average - dataPoint.fps_average).toFixed(2) + ')</b>';
		}
		
		var oneFps = '';
		if (dataPoint.fps_one > prevDataPoint.fps_one) {
			oneFps += '<b style="color:green;">(+' + (dataPoint.fps_one - prevDataPoint.fps_one).toFixed(2) + ')</b>';
		} else if (dataPoint.fps_one !== prevDataPoint.fps_one) {
			oneFps += '<b style="color:red;">(-' + (prevDataPoint.fps_one - dataPoint.fps_one).toFixed(2) + ')</b>';
		}
		
		return {
			avgFps:avgFps,
			oneFps:oneFps
		};
		 
	}
	
	function constructComponentForTtHtml(dataPoint, addClassStr, plottedPoints) {
		var compHtml = '<div>';
		
		var currentEquippedDp = currentEquippedDatapoint(plottedPoints);
		var diffSpans = currentEquippedDp ? contructComponentPerformanceDiffSpan(dataPoint, currentEquippedDp) : null;
		
		compHtml += '<b class="' + addClassStr + ' fg-' + dataPoint.perf_color + '"data-component-id="' + dataPoint.component_id + '">'
		+ dataPoint.component_display_name + '</b>';
		compHtml += '<br><b>MSRP: </b> $' + dataPoint.msrp;
		compHtml += '<br><b>Average Framerate:</b> ' + dataPoint.fps_average + ' fps on average ';
		compHtml += (diffSpans ? diffSpans.avgFps : '');
		compHtml += '<br><b>99th percentile:</b> ' + dataPoint.fps_one + ' fps 99% of the time ';
		compHtml += (diffSpans ? diffSpans.oneFps : '');
		compHtml += '<br><b>Benchmark:</b> ' + dataPoint.benchmark_name;
		
		compHtml += '</div>';
		return compHtml;
	}
	
	function constructTooltipDiv(divName, dataPoint, shapePosition, plottedPoints) {
		
		var otherPartsHtml = '<div id="tt-others"><hr><h5>Other parts in same price range:</h5>';
		var otherPartsExist = false;
		for (var i = 0; i < dataPoint.others.length; i++) {
			var otherComp = dataPoint.others[i];
			otherPartsHtml += constructComponentForTtHtml(otherComp, 'hover-other-part clickable', plottedPoints);
			otherPartsExist = true;
		}
		otherPartsHtml += '</div>';
		
		var ttHtml = '<div id="' + divName + '" class="chart-tt remove-click-away">';
		ttHtml += constructComponentForTtHtml(dataPoint, '', plottedPoints);
		ttHtml += '<div style="display:none" id="tt-equip-div"><hr><div><button class="ac-btn">Examine</button>';
		ttHtml += '<button id="equip-from-chart-btn" class="ac-btn" data-component-id="' + dataPoint.component_id + '">Equip</button>';
		ttHtml += '</div>';
		ttHtml += (otherPartsExist ? otherPartsHtml : '');
		ttHtml += '</div>';
		ttHtml += '</div>';
		
		var tt = $(ttHtml);
		tt.css('top', (shapePosition.top - 40) + 'px');
		tt.css('left', (shapePosition.left + 50) + 'px');
		
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
			if (toEquip && toEquip == dp.component_id) {
				outlineColor = 'rgb(255,255,255)';
			}
			else if (dp.component_id == currentRig['parts']['cpu_id'] && !toEquip) {
				outlineColor = 'rgb(255,255,255)';
			}
			
			var shape = createShape(dp, outlineColor);
			if (shape) shapes.push(shape);
			else continue;
			
			if (otherComponent && !otherRendered) {
				// iterate through other components:
				for (j=0; j < dp.others.length; j++) {
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
			trace1.y.push(dp.fps_average - ((dp.fps_average - dp.fps_one)/2));
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
				  range: [0,150]
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
		return {
			plottedPoints: plottedPoints,
			trace1: trace1,
			layout: layout
		};
	}
	
	var fpsData = null;
	function renderChart(genre, fpsDataIn){
		fpsData = fpsDataIn;
		var dataPoints = fpsData[genre] !== undefined ? fpsData[genre].datapoints : [];
		
		var chartData = generateChartData(dataPoints);

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
			
			// bind equip click event
			$('#equip-from-chart-btn').click(function(){
				equippableItemClicked($(this).data('component-id'));
				$('#chart-tooltip-div').remove();
				
				// render shapes (in case there are changes)
				chartData.layout.shapes = generateShapes(dataPoints, null);
				
				Plotly.plot('cpu-chart-tab', null, chartData.layout, {displayModeBar: false});
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
	
	$('.genre-select-btn').click(function(){
		var genre = $(this).data('genre');
		$('.genre-select-btn').removeClass('active');
		$(this).addClass('active');
		renderChart(genre, fpsData); // for now just pass in previously pulled data
	});
	
	//
	//
	// pull component FPS data when page loads (for now)
	$.getJSON( "/componentfps", function( data ) {
		// initially render FPS chart
		renderChart('FPS', data.fps_data);
	});
	
	//
	// remove any tooltip with class when it's not clicked on (or in)
	$(document).click(function(){
		$('.remove-click-away').remove();
	});
	
});