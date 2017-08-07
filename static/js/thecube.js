/*!
 * thecube.js v0.0.1
 * Copyright 2017 Second Mouse, Inc.
 */

(function(window) {
    
    "use strict";
    
    if (typeof jQuery === 'undefined') {
        throw new Error('thecube.js requires jQuery');
    }
    
    //
    // canvas('s) that have been initialized
    //
    var initializedCanvas = {};
    
    //
    //
    // initialized a canvas object inside the associated div
    //
    function initCanvasInDiv(divElmId) {
        
        if (initializedCanvas[divElmId]) return initializedCanvas[divElmId];
        
        var canvas = document.createElement('canvas');
        var div = document.getElementById(divElmId);

        canvas.id = "canvas_" + divElmId;
        canvas.width = div.clientWidth;
        canvas.height = div.clientHeight;
        
        div.appendChild(canvas);
        
        initializedCanvas[divElmId] = canvas;
        return canvas;
    }
    
    //
    // keeps track of bars rendered
    //
    var renderedBarsByElm = {};
    
    //
    // draws the passed in bars in the associated element
    //
    function drawBars(elmId, bars) {
        // the list of bars passed in are to be rendered on the canvas
        // this method will call the render function the necessary
        // number of times in order to animate the changing size of the bars
        
        // there are two bars for each genre
        // they both need to be animated?
        
        var renderedBars = renderedBarsByElm[elmId];
        if (!renderedBars) {
            renderedBars = {};
            renderedBarsByElm[elmId] = renderedBars;
        }
        
        if (Object.keys(renderedBars).length === 0) {
            // first render so populate with initial bars
            for (var i=0; i<bars.length; i++) {
                renderedBars[bars[i]['title']] = {};
                renderedBars[bars[i]['title']].fill = bars[i]['barFillFps'];
                renderedBars[bars[i]['title']].size = bars[i]['barSizeFps'];
            }
        }
        
        // now determine step size
        var stepCount = 30; // 60 fps and half second animation time
        var stepSizes = {};
        for (var i=0; i<bars.length; i++) {
            bars[i]['barFillStepSize'] = (bars[i]['barFillFps'] - renderedBars[bars[i]['title']].fill) / stepCount;
            bars[i]['barFillFpsBefore'] = renderedBars[bars[i]['title']].fill;
            
            bars[i]['barSizeStepSize'] = (bars[i]['barSizeFps'] - renderedBars[bars[i]['title']].size) / stepCount;
            bars[i]['barSizeFpsBefore'] = renderedBars[bars[i]['title']].size;
            
            renderedBars[bars[i]['title']].fill = bars[i]['barFillFps']; // update the old size
            renderedBars[bars[i]['title']].size = bars[i]['barSizeFps']; // update the old size
        }
        
        renderInsideElement(elmId, bars, 0, 30);
    }
    
    //
    // method to split text (for word-wrapping purposes)
    //
    function getLines(ctx, text, maxWidth) {
        var words = text.split(" ");
        var lines = [];
        var currentLine = words[0];

        for (var i = 1; i < words.length; i++) {
            var word = words[i];
            var width = ctx.measureText(currentLine + " " + word).width;
            if (width < maxWidth) {
                currentLine += " " + word;
            } else {
                lines.push(currentLine);
                currentLine = word;
            }
        }
        lines.push(currentLine);
        return lines;
    }
    
    //
    // rounded rectanges for bars
    //
    function roundRect(ctx, x, y, width, height, radius, fill, stroke) {
        if (typeof stroke == 'undefined') {
            stroke = true;
        }
        if (typeof radius === 'undefined') {
            radius = 5;
        }
        if (typeof radius === 'number') {
            radius = {tl: radius, tr: radius, br: radius, bl: radius};
        } else {
            var defaultRadius = {tl: 0, tr: 0, br: 0, bl: 0};
            for (var side in defaultRadius) {
                radius[side] = radius[side] || defaultRadius[side];
                }
        }
        ctx.beginPath();
        ctx.moveTo(x + radius.tl, y);
        ctx.lineTo(x + width - radius.tr, y);
        ctx.quadraticCurveTo(x + width, y, x + width, y + radius.tr);
        ctx.lineTo(x + width, y + height - radius.br);
        ctx.quadraticCurveTo(x + width, y + height, x + width - radius.br, y + height);
        ctx.lineTo(x + radius.bl, y + height);
        ctx.quadraticCurveTo(x, y + height, x, y + height - radius.bl);
        ctx.lineTo(x, y + radius.tl);
        ctx.quadraticCurveTo(x, y, x + radius.tl, y);
        ctx.closePath();
        if (fill) {
            ctx.fill();
        }
        if (stroke) {
            ctx.stroke();
        }
    }
    
    //
    // renders the canvas components
    //
    function renderInsideElement(elmId, bars, stepCount, maxSteps) {

        var canvas = initCanvasInDiv(elmId);

        var ctx = canvas.getContext('2d');
        
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        ctx.fillStyle = '#121526';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        for (var i=0; i<bars.length; i++){
            
            var barHeight = canvas.height * 0.04;
            var yPos = ((i + 1)/4) * canvas.height;
            var xPosText = 10;
            
            var xPosBar = canvas.width * (0.35);

            var maxBarWidth = (canvas.width * (0.65)) - 20;
            
            // determine proportion for this bar
            var barFill = bars[i].barFillFpsBefore + (stepCount * bars[i].barFillStepSize);
            var barFillProportion = (maxBarWidth / 200) * barFill;
            var barSize = bars[i].barSizeFpsBefore + (stepCount * bars[i].barSizeStepSize);
            var barSizeProportion = (maxBarWidth / 200) * barSize;
            
            
            ctx.fillStyle = 'black'; // background
            roundRect(ctx, xPosBar, yPos, maxBarWidth, barHeight, barHeight - 5, true, false);
            //ctx.fillRect(xPosBar, yPos, maxBarWidth, barHeight);
            
            ctx.fillStyle = '#460000'; // CPU
            roundRect(ctx, xPosBar, yPos, barSizeProportion, barHeight, barHeight - 5, true, false);
            //ctx.fillRect(xPosBar, yPos, barSizeProportion, barHeight);
            
            ctx.fillStyle = 'red'; // GPU
            roundRect(ctx, xPosBar, yPos, Math.min(barFillProportion, barSizeProportion), barHeight, barHeight - 5, true, false);
            //ctx.fillRect(xPosBar, yPos, Math.min(barFillProportion, barSizeProportion), barHeight);
            
            var fontSize = 13;
            ctx.font = fontSize + 'px \'Fjalla one\', sans-serif';
            ctx.textAlign = 'left';
            ctx.fillStyle = 'white';
            var textLines = getLines(ctx, bars[i].title, xPosBar - 20);
            for (var j=0; j<textLines.length; j++) {
                var textYPos = yPos + 9 + (j*fontSize);
                if (textLines.length > 1) textYPos = textYPos - (fontSize/2);
                ctx.fillText(textLines[j], 15, textYPos);
            }
        }
        
        var fontSize = 10;
        ctx.font = fontSize + 'px \'Fjalla one\', sans-serif';
        ctx.font = '10px';
        ctx.textAlign = 'right';
        ctx.fillStyle = 'white';
        ctx.fillText('200FPS Max', canvas.width - 5, 15);

        if (stepCount < maxSteps) window.setTimeout(renderInsideElement, 15, elmId, bars, stepCount + 1, maxSteps);
    }
    
    //
    // calls the server to get performance profile info and renders the new profile
    //
    function refreshProfile(canvasElmId, cpuId, gpuId) {
        
        // 
        
    }
    
    function defineTheCube() {
        var cubeLib = {};
        
        cubeLib.init = function(initObj) {
            // res1080pSelector (required)
            // res1440pSelector (required)
            // res2160pSelector (required)
            // profileCanvas (required)
            
            cubeLib.res1080pSelector = initObj.res1080pSelector;
            cubeLib.res1440pSelector = initObj.res1440pSelector;
            cubeLib.res2160pSelector = initObj.res2160pSelector;
            cubeLib.profileCanvas = initObj.profileCanvas;
            
        };
        
        cubeLib.processorSelected = function(processorId) {
            // call server to retrieve performance profile
            theCubeLib.cpu = processorId;
            refreshProfile(theCubeLib.);
        };
        
        cubeLib.graphicsCardSelected = function(graphicsCardId) {
            // call server to retrieve performance profile
        };
        
        return cubeLib;
    }
    
    if (typeof(TheCube) === 'undefined') {
            window.TheCube = defineTheCube();
    }

})(window);
