const options = {
    // Required: API key
    key: 'EbO6eL60QcWKnzXAtgH4SOYdLiCp7a7G', // REPLACE WITH YOUR KEY !!!

    // Put additional console output
    verbose: true,

    // Optional: Initial state of the map
    lat: 50.0,
    lon: -75.0,
    zoom: 5,
};

// Initialize Windy API
windyInit(options, windyAPI => {
    // windyAPI is ready, and contain 'map', 'store',
    // 'picker' and other usefull stuff

    const { map } = windyAPI;
    // .map is instance of Leaflet map
    windyAPI.store.on('isolines');

    L.popup()
        .setLatLng([50.0, -75.0])
        .setContent('Hello World')
        .openOn(map);
});
