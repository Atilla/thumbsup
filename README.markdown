# About Thumbsup #

Thumbsup is a simple website screenshot service. 

It uses the excellent http://phantomjs.org/ from Ariya Hidayat to
render websites to image files.

This projects embeds the 'urlnorm' URL normalisation routine, written
in Python by Mark Nottingham.

It requires ImageMagick for the image manipulation routines.

Thumbsup is built as a web-service using Tornado async web
server. Most of the code deals with spawning phantomjs and imagemagic
processes for getting the images and collecting the output of the
external calls. 

The images are served as static files and are cached - once generated,
a screenshot will persist until the file is removed. You can easily
use another web server for the static file handling, or just put
Thumbsup behind a Varnish proxy.  

Cache invalidation is easily done with a simple cron job that wipes
all files older than your cache period. 

Currently, the file storage methodology is quite naive and will not
scale with big amounts of files. 

# Usage #

Simply make a GET request to the specified port. The only required
parameter is *host* which is the URL of the page you want to render. 

Optionally you can specify the viewport size *view_size*, to which the image will
be rendered and cropped and *thumb_size* which are the dimensions to
which the rendered screenshot will be resized to. By default those
values are '1280x1024' and '320x200', respectively. 
