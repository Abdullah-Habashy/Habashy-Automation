
// Auto-generated script to add markers

var timestamps = [
    "00:00:10"
];

function timeToSeconds(timeStr) {
    var parts = timeStr.split(':').reverse();
    var seconds = 0;
    for (var i = 0; i < parts.length; i++) {
        seconds += parseFloat(parts[i]) * Math.pow(60, i);
    }
    return seconds;
}

function addMarkers() {
    var project = app.project;
    if (!project) {
        alert("No project open.");
        return;
    }

    var sequence = project.activeSequence;
    if (!sequence) {
        alert("No active sequence. Please open a sequence.");
        return;
    }

    var markers = sequence.markers;
    var successCount = 0;

    for (var i = 0; i < timestamps.length; i++) {
        var timeStr = timestamps[i].toString();
        var timeInSeconds = 0;

        if (timeStr.indexOf(':') > -1) {
            timeInSeconds = timeToSeconds(timeStr);
        } else {
            timeInSeconds = parseFloat(timeStr);
        }

        if (isNaN(timeInSeconds)) {
            continue;
        }

        var newMarker = markers.createMarker(timeInSeconds);
        newMarker.name = "Marker " + (i + 1);
        newMarker.comments = "Auto-added";
        newMarker.setColorIndex(1); // Red
        
        successCount++;
    }
    
    alert("Added " + successCount + " red markers.");
}

addMarkers();
