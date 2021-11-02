# Code adapted from the Adafruit_Python_SSD1306 library's examples.
# https://github.com/adafruit/Adafruit_Python_SSD1306
# 
# Copyright (c) 2017 Adafruit Industries
# Author: Tony DiCola & James DeVito
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import time

import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


class Display:
    """Wrapper class for displaying text on OLED 0.96" display 128x64"""

    RST = None

    def __init__(self, fontsize=24, bg_color=0):
        self.fontsize=fontsize
        self.font = ImageFont.truetype('Quicksand-Medium.ttf', self.fontsize)
        self.bg_color = bg_color
        self.disp = Adafruit_SSD1306.SSD1306_128_32(rst=self.RST)
        self.disp.begin()
        # clear display
        self.disp.clear()
        self.disp.display()
        # create blank image for drawing
        self.width = self.disp.width
        self.height = self.disp.height
        self.image = Image.new('1', (self.width, self.height))
        # get drawing object to draw on image
        self.draw = ImageDraw.Draw(self.image)
        # draw black filled box to clear the image
        self.draw.rectangle((0,0,self.width,self.height), outline=0, fill=self.bg_color)

    def _change_fontsize(self, font_size):
        self.fontsize = font_size
        self.font = ImageFont.truetype('Quicksand-Medium.ttf', self.fontsize)

    def show(self, txt, loc='center', font_size=24):
        if font_size != self.fontsize:
            self._change_fontsize(font_size)
        self.draw.rectangle((0,0,self.width,self.height), outline=0, fill=0)
        w, h = self.draw.textsize(txt, font=self.font)
        if loc == 'center':
            loc = ((self.width - w)/2, (self.height-h)/2)
        elif loc == 'top-left':
            loc = (0, 0)
        elif loc == 'center-left':
            loc = (0, (self.height-h)/2)
        self.draw.text(loc, txt, font=self.font, fill=255)
        self.disp.image(self.image)
        self.disp.display()

    def countdown(self, seconds=15):
        for i in range(15, 0, -1):
            txt = str(i)
            w, h = self.draw.textsize(txt, font=self.font)   
            loc = ((self.width - w)/2, (self.height-h)/2)
            self.show(txt, 'center')
            time.sleep(1)
    
    def clear(self):
        self.disp.clear()
        self.disp.display()


if __name__ == '__main__':
    display = Display()
    txt = 'Heart Rate'
    display.show(txt, 'center')
    time.sleep(1)
    display.countdown(15)

    txt = 'SpO2'
    display.show(txt, 'center')
    time.sleep(1)
    display.countdown(15)

    display.font_size(12)
    txt = 'HR: {} bpm\nSpO2: {} %'.format(56.8, 97.9)
    display.show(txt, 'center')
