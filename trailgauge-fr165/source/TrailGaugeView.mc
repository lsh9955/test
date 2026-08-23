using Toybox.Graphics as Gfx;
using Toybox.Math as Math;
using Toybox.UserProfile as UserProfile;
using Toybox.WatchUi as WatchUi;

class TrailGaugeView extends WatchUi.DataField {
    var _distanceM;
    var _heartRate;
    var _altitudeM;
    var _timerMs;
    var _location;
    var _routeIndex;
    var _hrZones;
    var _lastZone;
    var _zoneStartMs;

    var _minX;
    var _maxX;
    var _minY;
    var _maxY;
    var _minEle;
    var _maxEle;

    function initialize() {
        DataField.initialize();

        _distanceM = 0.0;
        _heartRate = null;
        _altitudeM = null;
        _timerMs = 0;
        _location = null;
        _routeIndex = 0;
        _lastZone = 0;
        _zoneStartMs = 0;
        _hrZones = null;

        _scanRouteBounds();
        _loadHeartRateZones();
    }

    function _loadHeartRateZones() {
        try {
            _hrZones = UserProfile.getHeartRateZones(UserProfile.HR_ZONE_SPORT_RUNNING);
        } catch (e) {
            _hrZones = null;
        }
    }

    function _scanRouteBounds() {
        if (!RouteData.hasRoute()) {
            _minX = 0.0; _maxX = 1.0;
            _minY = 0.0; _maxY = 1.0;
            _minEle = 0.0; _maxEle = 1.0;
            return;
        }

        _minX = RouteData.X[0]; _maxX = RouteData.X[0];
        _minY = RouteData.Y[0]; _maxY = RouteData.Y[0];
        _minEle = RouteData.ELE[0]; _maxEle = RouteData.ELE[0];

        for (var i = 1; i < RouteData.size(); i += 1) {
            if (RouteData.X[i] < _minX) { _minX = RouteData.X[i]; }
            if (RouteData.X[i] > _maxX) { _maxX = RouteData.X[i]; }
            if (RouteData.Y[i] < _minY) { _minY = RouteData.Y[i]; }
            if (RouteData.Y[i] > _maxY) { _maxY = RouteData.Y[i]; }
            if (RouteData.ELE[i] < _minEle) { _minEle = RouteData.ELE[i]; }
            if (RouteData.ELE[i] > _maxEle) { _maxEle = RouteData.ELE[i]; }
        }

        if ((_maxX - _minX) < 1.0) { _maxX = _minX + 1.0; }
        if ((_maxY - _minY) < 1.0) { _maxY = _minY + 1.0; }
        if ((_maxEle - _minEle) < 1.0) { _maxEle = _minEle + 1.0; }
    }

    function compute(info) {
        if (info.elapsedDistance != null) {
            _distanceM = info.elapsedDistance;
        }
        if (info.currentHeartRate != null) {
            _heartRate = info.currentHeartRate;
        } else {
            _heartRate = null;
        }
        if (info.altitude != null) {
            _altitudeM = info.altitude;
        } else {
            _altitudeM = null;
        }
        if (info.elapsedTime != null) {
            _timerMs = info.elapsedTime;
        }
        if (info.currentLocation != null) {
            _location = info.currentLocation;
            _routeIndex = _nearestRouteIndex(_location);
        } else {
            _location = null;
            _routeIndex = _indexForDistance(_distanceM);
        }

        var zone = _getHrZone(_heartRate);
        if (zone != _lastZone) {
            _lastZone = zone;
            _zoneStartMs = _timerMs;
        }

        return null;
    }

    function onUpdate(dc) {
        dc.setColor(0xFFFFFF, 0x000000);
        dc.clear();

        var w = dc.getWidth();
        var h = dc.getHeight();

        // This UI is intentionally designed for a one-field, full-screen layout.
        if (w < 300 || h < 300) {
            _drawCompact(dc, w, h);
            return;
        }

        _drawHeader(dc, w);
        _drawRouteMap(dc, 44, 49, w - 88, 103);
        _drawElevation(dc, 44, 171, w - 88, 102);
        _drawBottomMetrics(dc, w);
    }

    function _drawHeader(dc, w) {
        dc.setColor(0xB8B8B8, 0x000000);
        dc.drawText(w / 2, 22, Gfx.FONT_XTINY, RouteData.NAME, Gfx.TEXT_JUSTIFY_CENTER);
    }

    function _drawCompact(dc, w, h) {
        var hrText = (_heartRate == null) ? "--" : _heartRate.format("%d");
        var zone = _getHrZone(_heartRate);
        dc.setColor(0xFFFFFF, 0x000000);
        dc.drawText(w / 2, h / 2 - 24, Gfx.FONT_SMALL, _formatKm(_distanceM) + " km", Gfx.TEXT_JUSTIFY_CENTER);
        dc.drawText(w / 2, h / 2 + 4, Gfx.FONT_TINY, "HR " + hrText + "  Z" + zone.format("%d"), Gfx.TEXT_JUSTIFY_CENTER);
    }

    function _drawRouteMap(dc, x, y, w, h) {
        dc.setColor(0x8B8B8B, 0x000000);
        dc.drawText(x, y - 18, Gfx.FONT_XTINY, "ROUTE", Gfx.TEXT_JUSTIFY_LEFT);

        if (!RouteData.hasRoute()) {
            dc.drawText(x + w / 2, y + h / 2, Gfx.FONT_TINY, "NO GPX", Gfx.TEXT_JUSTIFY_CENTER);
            return;
        }

        var rx = _maxX - _minX;
        var ry = _maxY - _minY;
        var sx = w.toFloat() / rx;
        var sy = h.toFloat() / ry;
        var scale = (sx < sy) ? sx : sy;
        var usedW = rx * scale;
        var usedH = ry * scale;
        var ox = x + ((w - usedW) / 2.0);
        var oy = y + ((h - usedH) / 2.0);

        // Whole GPX trace.
        dc.setColor(0x707070, 0x000000);
        for (var i = 1; i < RouteData.size(); i += 1) {
            var x1 = ox + (RouteData.X[i - 1] - _minX) * scale;
            var y1 = oy + usedH - (RouteData.Y[i - 1] - _minY) * scale;
            var x2 = ox + (RouteData.X[i] - _minX) * scale;
            var y2 = oy + usedH - (RouteData.Y[i] - _minY) * scale;
            dc.drawLine(x1.toNumber(), y1.toNumber(), x2.toNumber(), y2.toNumber());
        }

        // Remaining route is brighter than the completed section.
        dc.setColor(0xFFFFFF, 0x000000);
        for (var j = _routeIndex + 1; j < RouteData.size(); j += 1) {
            var ax = ox + (RouteData.X[j - 1] - _minX) * scale;
            var ay = oy + usedH - (RouteData.Y[j - 1] - _minY) * scale;
            var bx = ox + (RouteData.X[j] - _minX) * scale;
            var by = oy + usedH - (RouteData.Y[j] - _minY) * scale;
            dc.drawLine(ax.toNumber(), ay.toNumber(), bx.toNumber(), by.toNumber());
        }

        var cx = ox + (RouteData.X[_routeIndex] - _minX) * scale;
        var cy = oy + usedH - (RouteData.Y[_routeIndex] - _minY) * scale;
        dc.setColor(0x00D9FF, 0x000000);
        dc.fillCircle(cx.toNumber(), cy.toNumber(), 5);
        dc.setColor(0xFFFFFF, 0x000000);
        dc.drawCircle(cx.toNumber(), cy.toNumber(), 7);
    }

    function _drawElevation(dc, x, y, w, h) {
        dc.setColor(0x8B8B8B, 0x000000);
        dc.drawText(x, y - 17, Gfx.FONT_XTINY, "ELEVATION", Gfx.TEXT_JUSTIFY_LEFT);

        if (!RouteData.hasRoute()) {
            return;
        }

        var total = RouteData.DIST[RouteData.size() - 1];
        if (total < 1.0) { total = 1.0; }
        var er = _maxEle - _minEle;

        dc.setColor(0x707070, 0x000000);
        for (var i = 1; i < RouteData.size(); i += 1) {
            var x1 = x + (RouteData.DIST[i - 1] / total) * w;
            var y1 = y + h - ((RouteData.ELE[i - 1] - _minEle) / er) * h;
            var x2 = x + (RouteData.DIST[i] / total) * w;
            var y2 = y + h - ((RouteData.ELE[i] - _minEle) / er) * h;
            dc.drawLine(x1.toNumber(), y1.toNumber(), x2.toNumber(), y2.toNumber());
        }

        dc.setColor(0xFFFFFF, 0x000000);
        for (var j = _routeIndex + 1; j < RouteData.size(); j += 1) {
            var ax = x + (RouteData.DIST[j - 1] / total) * w;
            var ay = y + h - ((RouteData.ELE[j - 1] - _minEle) / er) * h;
            var bx = x + (RouteData.DIST[j] / total) * w;
            var by = y + h - ((RouteData.ELE[j] - _minEle) / er) * h;
            dc.drawLine(ax.toNumber(), ay.toNumber(), bx.toNumber(), by.toNumber());
        }

        var curX = x + (RouteData.DIST[_routeIndex] / total) * w;
        var curY = y + h - ((RouteData.ELE[_routeIndex] - _minEle) / er) * h;
        dc.setColor(0x00D9FF, 0x000000);
        dc.drawLine(curX.toNumber(), y, curX.toNumber(), y + h);
        dc.fillCircle(curX.toNumber(), curY.toNumber(), 4);

        dc.setColor(0x8B8B8B, 0x000000);
        dc.drawText(x, y + h + 2, Gfx.FONT_XTINY, _minEle.toNumber().format("%d") + "m", Gfx.TEXT_JUSTIFY_LEFT);
        dc.drawText(x + w, y + h + 2, Gfx.FONT_XTINY, _maxEle.toNumber().format("%d") + "m", Gfx.TEXT_JUSTIFY_RIGHT);
    }

    function _drawBottomMetrics(dc, w) {
        var zone = _getHrZone(_heartRate);
        var hrText = (_heartRate == null) ? "--" : _heartRate.format("%d");
        var altText = (_altitudeM == null) ? "--" : _altitudeM.toNumber().format("%d");
        var effort = _getEffort(zone);

        dc.setColor(0xB8B8B8, 0x000000);
        dc.drawText(67, 301, Gfx.FONT_XTINY, "DIST", Gfx.TEXT_JUSTIFY_CENTER);
        dc.drawText(w / 2, 301, Gfx.FONT_XTINY, "HR", Gfx.TEXT_JUSTIFY_CENTER);
        dc.drawText(w - 67, 301, Gfx.FONT_XTINY, "ALT", Gfx.TEXT_JUSTIFY_CENTER);

        dc.setColor(0xFFFFFF, 0x000000);
        dc.drawText(67, 321, Gfx.FONT_SMALL, _formatKm(_distanceM), Gfx.TEXT_JUSTIFY_CENTER);
        dc.drawText(w / 2, 321, Gfx.FONT_SMALL, hrText, Gfx.TEXT_JUSTIFY_CENTER);
        dc.drawText(w - 67, 321, Gfx.FONT_SMALL, altText, Gfx.TEXT_JUSTIFY_CENTER);

        dc.setColor(_effortColor(effort), 0x000000);
        dc.drawText(w / 2, 354, Gfx.FONT_TINY, "Z" + zone.format("%d") + "  " + effort, Gfx.TEXT_JUSTIFY_CENTER);
    }

    function _getHrZone(hr) {
        if (hr == null || _hrZones == null || _hrZones.size() < 6) {
            return 0;
        }
        if (hr < _hrZones[0]) { return 0; }
        if (hr <= _hrZones[1]) { return 1; }
        if (hr <= _hrZones[2]) { return 2; }
        if (hr <= _hrZones[3]) { return 3; }
        if (hr <= _hrZones[4]) { return 4; }
        return 5;
    }

    function _getEffort(zone) {
        if (zone == 0) { return "NO HR"; }
        if (zone <= 2) { return "EASY"; }
        if (zone == 3) { return "STEADY"; }
        if (zone == 4) {
            var held = _timerMs - _zoneStartMs;
            return (held >= 180000) ? "BACK OFF" : "HARD";
        }
        return "TOO HARD";
    }

    function _effortColor(effort) {
        if (effort == "EASY" || effort == "STEADY") { return 0x57E389; }
        if (effort == "HARD") { return 0xFFD166; }
        if (effort == "BACK OFF" || effort == "TOO HARD") { return 0xFF6B6B; }
        return 0xB8B8B8;
    }

    function _nearestRouteIndex(location) {
        if (!RouteData.hasRoute()) { return 0; }
        var deg = location.toDegrees();
        var x = (deg[1] - RouteData.BASE_LON) * RouteData.LON_M_PER_DEG;
        var y = (deg[0] - RouteData.BASE_LAT) * RouteData.LAT_M_PER_DEG;

        var start = _routeIndex - 20;
        if (start < 0) { start = 0; }
        var finish = _routeIndex + 45;
        if (finish >= RouteData.size()) { finish = RouteData.size() - 1; }

        // On first fix, or near a search-window edge, scan the full route.
        if (_timerMs < 3000 || _routeIndex == start || _routeIndex == finish) {
            start = 0;
            finish = RouteData.size() - 1;
        }

        var best = start;
        var bestD2 = 999999999999.0;
        for (var i = start; i <= finish; i += 1) {
            var dx = RouteData.X[i] - x;
            var dy = RouteData.Y[i] - y;
            var d2 = dx * dx + dy * dy;
            if (d2 < bestD2) {
                bestD2 = d2;
                best = i;
            }
        }
        return best;
    }

    function _indexForDistance(distanceM) {
        if (!RouteData.hasRoute()) { return 0; }
        var best = 0;
        for (var i = 1; i < RouteData.size(); i += 1) {
            if (RouteData.DIST[i] > distanceM) {
                break;
            }
            best = i;
        }
        return best;
    }

    function _formatKm(meters) {
        var tenths = Math.round(meters / 100.0);
        var whole = (tenths / 10).toNumber();
        var decimal = (tenths - (whole * 10)).toNumber();
        return whole.format("%d") + "." + decimal.format("%d");
    }
}
