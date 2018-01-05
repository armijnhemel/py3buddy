# py3buddy
Python 3 code to work with the iBuddy MSN figurine released under the GPL-3.0 license.

* py3buddy.py -- main file with class
* py3buddydemo.py -- demo code
* py3buddy.config -- example configuration file
* 99-ibuddy.rules -- udev rules for iBuddy with productid 0x0002 and 0x0004

This code has been tested with iBuddy devices with USB product id 0x0002
(regular) and 0x0004 (iBuddy Twins). There are apparently more iBuddy devices
out there with different product ids (0x0001 is known, but there are rumours
that there are also devices with 0x0006).

The following devices have not been tested with:

* iBuddy black/white
* iBuddy Angel
* iBuddy Devil
* iBuddy Molly (if ever released)

This code was inspired by pybuddy (especially the idea for a macro language,
although the original product also had something like this), but no code was
copied. The code for pybuddy can be found here (note: the original Google code
site seems to gone):

https://github.com/ewall/pybuddy/

The original version of pybuddy came with the following notice:

pybuddy: Python daemon to control your i-buddy USB device

by luis.peralta, Jose.Carlos.Luna, and leandro.vazquez
released under MIT License (http://www.opensource.org/licenses/mit-license.php)
