/* The following structure:

Testing sets
{x: 10, y: 10, col: WHITE, temp: 21},
{x: -7, y: 19, col: BLUE, temp: 25.5}, 
{x: 0, y: -4, col: RED, temp: 18.9}

Adapted to format
{"x": 10, "y": 10, "color": "white", "size": "small", "temp": 21},
{"x": -7, "y": 19, "color": "blue", "size": "small", "temp": 25.5}, 
{"x": 0, "y": -4, "color": "red", "size": "large", "temp": 18.9}

Then sending via ESP32 UART Robot to UI comms receiver ('/sample' topic)

Mapping of the relevant data correctly on the UI displayed

done
*/