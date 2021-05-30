import requests
import time
from PIL import Image
import typing
import math
from rich.progress import track
import datetime

class OutOfBoundsException(Exception):
    """
    An exception class to use whenever input is out of bounds
    """
    pass

class Client:
    """
    A client that does all the requests and rate limit handling for you.
    """

    def __init__(self, token):
        self.token = token
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.__http = requests.Session()
        self.base = "https://pixels.pythondiscord.com"

        with self.__http.head(self.base + "/set_pixel", headers=self.headers) as resp:
            headers = resp.headers
            try:
                self.post_limit = headers["requests-remaining"]
            except KeyError:
                self.post_limit = 0
            if self.post_limit < headers["requests-limit"]:
                self.post_timeout = datetime.datetime.now() + datetime.timedelta(seconds=float(headers['requests-reset']))
            else:
                self.post_timeout = datetime.datetime.now()

        with self.__http.head(self.base + "/get_pixel", headers=self.headers) as resp:
            headers = resp.headers
            try:
                self.get_limit = headers["requests-remaining"]
            except KeyError:
                self.get_limit = 0
            if self.get_limit < headers["requests-limit"]:
                self.get_timeout = datetime.datetime.now() + datetime.timedelta(seconds=float(headers['requests-reset']))
            else:
                self.get_timeout = datetime.datetime.now()

        with self.__http.head(self.base + "/get_pixels", headers=self.headers) as resp:
            headers = resp.headers
            try:
                self.gets_limit = headers["requests-remaining"]
            except KeyError:
                self.gets_limit = 0
            if self.gets_limit < headers["requests-limit"]:
                self.gets_timeout = datetime.datetime.now() + datetime.timedelta(seconds=float(headers['requests-reset']))
            else:
                self.gets_timeout = datetime.datetime.now()

    def get_pixel(self, x: int, y: int):
        """
        Returns the hexadecimal color code of the given pixel
        
        Params:
        x: int - The x position of the pixel
        y: int - The y position of the pixel

        Returns:
        int - The color of the requested pixel
        """

        if self.get_limit == 0 and self.get_timeout > datetime.datetime.now():
            timer = self.get_timeout - datetime.datetime.now()
            for n in track(range(int(timer.total_seconds()) + 1), "[cyan bold]Awaiting /get_pixel rate limit.."):
                time.sleep(1)

        with self.__http.get(self.base + "/get_size", headers=self.headers) as resp:
            data = resp.json()
            size = (data["width"], data["height"])
            if x > size[0] or y > size[1]:
                raise OutOfBoundsException("The selected pixel is out of bounds")

        data = {
            "x": x,
            "y": y
        }

        with self.__http.get(self.base + "/get_pixel", headers = self.headers, params=data) as resp:
            data = resp.json()
            headers = resp.headers
            try:
                self.get_limit = int(headers["requests-remaining"])
                self.get_timeout = datetime.datetime.now() + datetime.timedelta(seconds=float(headers['requests-reset']))
            except KeyError:
                self.get_limit = 0
                self.get_timeout = datetime.datetime.now() + datetime.timedelta(seconds=float(headers['cooldown-reset']))
            return int(f"0x{data['rgb']}", base=16)
    
    def get_canvas(self, scale=1):
        """
        Fetch the entire canvas and returns it as a pillow Image instance. Optionally resize it by a scale factor

        Params:
        scale: int - A factor to resize the image by

        Returns:
        pillow.Image - The current canvas
        """
        if scale <=0:
            raise TypeError("Scale must be a positive integer")
        if self.gets_limit == 0 and self.gets_timeout > datetime.datetime.now():
            timer = self.gets_timeout - datetime.datetime.now()
            for n in track(range(int(timer.total_seconds()) + 1), "[cyan bold]Awaiting /get_canvas rate limit.."):
                time.sleep(1)
        with self.__http.get(self.base + "/get_pixels", headers=self.headers) as resp:
            headers = resp.headers
            try:
                self.gets_limit = int(headers["requests-remaining"])
                self.gets_timeout = datetime.datetime.now() + datetime.timedelta(seconds=float(headers['requests-reset']))
            except KeyError:
                self.gets_limit = 0
                self.gets_timeout = datetime.datetime.now() + datetime.timedelta(seconds=float(headers['cooldown-reset']))
            with self.__http.get(self.base + "/get_size", headers= self.headers) as resps:
                size = resps.json()
                im =  Image.frombytes(mode="RGB", size=(size['width'], size['height']), data=resp.content)
                im = im.resize((im.size[0]*scale, im.size[1]*scale), Image.NEAREST)
                return im



    
    def get_size(self):
        """
        Returns the size of the canvas

        Params:
        None

        Returns:
        tuple - The width and height of the canvas
        """
        with self.__http.get(self.base + "/get_size", headers=self.headers) as resp:
            data = resp.json()
            return (data["width"], data["height"])

    def set_pixel(self, x: int, y: int, color: typing.Union[int, str]):
        """
        Sets a pixel on the canvas

        Params:
        x: int - The x position of the pixel
        y: int - The y position of the pixel
        color: int/str - the RGB colorcode of the pixel

        Returns:
        None
        """
        if isinstance(color, str):
            color = color.removeprefix("0x")
            if len(color) != 6:
                raise TypeError(f"Invalid color '{color}'")
        else:
            color = hex(color)[2:].upper()
        with self.__http.get(self.base + "/get_size", headers=self.headers) as resp:
            data = resp.json()
            size = (data["width"], data["height"])
            if x > size[0] or y > size[1] or x < 0 or y < 0:
                raise OutOfBoundsException("The selected pixel is out of bounds")

        data = {
            "x": x,
            "y": y,
            "rgb": color
        }

        curcolor = self.get_pixel(x, y)
        if data["rgb"] == hex(curcolor)[2:]:
            return

        if len(data["rgb"]) > 6:
            raise TypeError("The given color is invalid")
        elif len(data["rgb"]) < 6:
            while len(data["rgb"]) < 6:
                data["rgb"] = "0" + data["rgb"]
        if self.post_limit == 0 and self.post_timeout > datetime.datetime.now():
            timer = self.post_timeout - datetime.datetime.now()
            for n in track(range(int(timer.total_seconds()) + 1), "[cyan bold]Awaiting /set_pixel rate limit.."):
                time.sleep(1)
        with self.__http.post(self.base + "/set_pixel", headers=self.headers, json=data) as resp:
            headers = resp.headers
            try:
                self.post_limit = int(headers["requests-remaining"])
                self.post_timeout = datetime.datetime.now() + datetime.timedelta(seconds=float(headers['requests-reset']))
            except KeyError:
                self.post_limit = 0
                self.post_timeout = datetime.datetime.now() + datetime.timedelta(seconds=float(headers['cooldown-reset']))
            return

    def get_limits(self):
        """
        Return the last known rate limits of the API. These are refreshed every request.

        Params:
        None

        Returns:
        dict - A dictionary with the rate limits formatted as follow
            "set_pixel": tuple(remaining, timeout)
            "get_pixel": tuple(remaining, timeout)
            "get_canvas": tuple(remaining, timeout)
        """
        limits = {
            "set_pixel": (self.post_limit, self.post_timeout),
            "get_pixel": (self.get_limit, self.get_timeout),
            "get_canvas": (self.gets_limit, self.gets_timeout)
        }
        return limits

    def set_picture(self, ox: int, oy: int, img: typing.Union[str, Image.Image]):
        """
        Starts a job to add a picture with offset x an y. Img can either be a file directory, an direct URL (Only HTTP supported) or a pillow.Image

        Params:
        ox: int - The x offset
        oy: int- The y offset
        img: typing.Union[str, pillow.Image.Image] - The image to upload. Can either be a path, a HTTP direct image link or a pillow image instance

        Returns:
        None
        """
        if isinstance(img, str):                        
            if img.startswith(("http://", "https://")):
                with self.__http.get(img, stream=True) as r:
                    if r.status_code == 200:
                        image = Image.open(r.raw)
                    else:
                        raise TypeError("The given image could not be found")
            else:
                try:
                    image = Image.open(img)
                except OSError:
                    raise TypeError("The given image could not be found")

        else:
            image = img

        with self.__http.get(self.base + "/get_size", headers=self.headers) as resp:
            data = resp.json()
            size = (data["width"], data["height"])
            if ox + image.width > size[0] or oy + image.height > size[1] or ox < 0 or oy < 0:
                raise OutOfBoundsException("The image is out of bounds")
        
        for x in range(image.width):
            for y in range(image.height):
                color = image.getpixel((x,y))
                r = color[0]
                g = color[1]
                b = color[2]
                try:
                    a = color[3]
                except IndexError:
                    a = 255
                if a == 0:
                    continue
                color = f"{r:02X}{g:02X}{b:02X}"
                cur = self.get_pixel(x + ox,y + oy)
                if cur == int(color, base=16):
                    continue

                self.set_pixel(x, y, color)

