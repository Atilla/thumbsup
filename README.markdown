Thumbsup is a simple website screenshot service. 

It uses the excellent http://phantomjs.org/ from Ariya Hidayat to
render websites to image files.

It requires ImageMagick for the image manipulation routines.

Thumbsup is built as a web-service using Tornado async web
server. Most of the code deals with spawning phantomjs and imagemagic
processes for getting the images. 

The images are served as static files and are cached - once generated,
a screenshot will persist until the file is removed. You can easily
use another web server for the static file handling, or just put
Thumbsup behind a Varnish proxy.  

Cache invalidation is easily done with a simple cron job that wipes
all files older than your cache period. 

Currently, the file storage methodology is quite naive and will not
scale with big amounts of files. 
