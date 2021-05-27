import requests
import time
from PIL import Image
import typing
from io import BytesIO

class RateLimitException(Exception):
    """
    An exception class to use whenever cooldown occurs
    """
    pass

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
        self.post_limit = 1
        self.post_timeout = 1
        self.get_limit = 1
        self.get_timeout = 1
        self.gets_limit = 1
        self.gets_timeout = 1
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.__http = requests.Session()
        self.base = "https://pixels.pythondiscord.com"

    def get_pixel(self, x: int, y: int):
        """
        Returns the hexadecimal color code of the given pixel
        
        Params:
        x: int - The x position of the pixel
        y: int - The y position of the pixel

        Returns:
        int base 16 - The color of the requested pixel
        """

        if self.get_limit == 0:
            time.sleep(self.get_timeout + 1)

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
                self.get_timeout = int(headers["requests-reset"])
            except KeyError:
                self.get_limit = 0
                self.get_timeout = int(headers['cooldown-reset'])
                raise RateLimitException(f"Rate limited by server but internal values not updated. Please wait {self.get_timeout}")
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
        if self.gets_limit == 0:
            time.sleep(self.gets_timeout+ 1)
        with self.__http.get(self.base + "/get_pixels", headers=self.headers) as resp:
            stream = bytes(resp.content)
            headers = resp.headers
            try:
                self.gets_limit = int(headers["requests-remaining"])
                self.gets_timeout = int(headers["requests-reset"])
            except KeyError:
                self.gets_limit = 0
                self.gets_timeout = int(headers['cooldown-reset'])
                raise RateLimitException(f"Rate limited by server but internal values not updated. Please wait {self.gets_timeout}")
            with self.__http.get(self.base + "/get_size", headers= self.headers) as resps:
                size = resps.json()
                im =  Image.frombytes(mode="RGB", size=(size['width'], size['height']), data=stream)
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

    def set_pixel(self, x: int, y: int, color: int):
        """
        Sets a pixel on the canvas

        Params:
        x: int - The x position of the pixel
        y: int - The y position of the pixel
        color: int - the RGB colorcode of the pixel

        Returns:
        None
        """

        with self.__http.get(self.base + "/get_size", headers=self.headers) as resp:
            data = resp.json()
            size = (data["width"], data["height"])
            if x > size[0] or y > size[1]:
                raise OutOfBoundsException("The selected pixel is out of bounds")

        data = {
            "x": x,
            "y": y,
            "rgb": hex(color)[2:].upper()
        }

        with self.__http.get(self.base + "/get_pixel", headers=self.headers, params={"x": x, "y": y}) as resp:
            jdata = resp.json()
            if data["rgb"] == jdata["rgb"]:
                return

        if len(data["rgb"]) > 6:
            raise TypeError("The given color is too long")
        elif len(data["rgb"]) < 6:
            while len(data["rgb"]) < 6:
                data["rgb"] = "0" + data["rgb"]
        if self.post_limit == 0:
            time.sleep(self.post_timeout + 1)
        with self.__http.post(self.base + "/set_pixel", headers=self.headers, json=data) as resp:
            headers = resp.headers
            try:
                self.post_limit = int(headers["requests-remaining"])
                self.post_timeout = int(headers["requests-reset"])
            except KeyError:
                self.post_limit = 0
                self.post_timeout = int(headers['cooldown-reset'])

                raise RateLimitException(f"Rate limited by server but internal values not updated. Please wait {self.post_timeout}")
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

    def set_picture(self, x: int, y: int, img: typing.Union[str, Image.Image]):
        """
        Starts a job to add a picture with offset x an y. Img can either be a file directory, an direct URL (Only HTTP supported) or a pillow.Image

        Params:
        x: int - The x offset
        y: int- The y offset
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
            if x + image.width > size[0] or y + image.height > size[1]:
                raise OutOfBoundsException("The image is out of bounds")
        
        for x in range(image.width):
            for y in range(image.height):
                r, g, b, a = image.getpixel((x,y))
                if a == 0:
                    continue
                color = hex(r)[2:] + hex(g)[2:] + hex(b)[2:]
                cur = self.get_pixel(x,y)
                if cur == int(color, base=16):
                    continue

                self.set_pixel(x, y, int(color, base=16))

