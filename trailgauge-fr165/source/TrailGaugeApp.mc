using Toybox.Application as App;

class TrailGaugeApp extends App.AppBase {
    function initialize() {
        AppBase.initialize();
    }

    function getInitialView() {
        return [ new TrailGaugeView() ];
    }
}
