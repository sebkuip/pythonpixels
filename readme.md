# Pythonpixels

*An API wrapper for the python discord pixels project*

## Requirements

pillow and request are required for this library

## Usage

### Getting started

First make an instance of the Client class and pass your token to the contructor.
Everything in this library is done from the Client class.

```py
import pythonpixels

client = pythonpixels.Client("TOKEN") # Your token must be inserted where it says TOKEN
```

### Methods

```py
client.get_pixel(x, y)
```

Returns the hexadecimal color code of the given pixel
    
Params:
x: int - The x position of the pixel
y: int - The y position of the pixel

Returns:
int base 16 - The color of the requested pixel

```py
client.get_canvas(scale)
```

Fetch the entire canvas and returns it as a pillow Image instance. Optionally resize it by a scale factor

Params:
scale: int - A factor to resize the image by

Returns:
pillow.Image - The current canvas

```py
client.get_size()
```

Returns the size of the canvas

Params:
None

Returns:
tuple - The width and height of the canvas

```py
client.set_pixel(x, y, color)
```

Sets a pixel on the canvas

Params:
x: int - The x position of the pixel
y: int - The y position of the pixel
color: int - the RGB colorcode of the pixel

Returns:
None

```py
client.get_limits()
```

Return the last known rate limits of the API. These are refreshed every request.

Params:
None

Returns:
dict - A dictionary with the rate limits formatted as follow
"set_pixel": tuple(remaining, timeout)
"get_pixel": tuple(remaining, timeout)
"get_canvas": tuple(remaining, timeout)