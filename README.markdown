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


# File Storage #

You can choose between two ways to store your files.

* All in one folder, filename being the hash of the URL and render sizes
* Slightly more elaborate two-level folder scheme, in order to fit a large number of files.

The first file storage methodology is quite naive and will not
scale with big amounts of files for obvious reasons. The service will
automatically use the second storage scheme, if it detects more than
two subfolders in the static files folder. Don't forget you will need
the right permissions for the destination folder.


# Usage #

Simply make a GET request to the specified port. The only required
parameter is *host* which is the URL of the page you want to render. 

Optionally you can specify the viewport size *view_size*, to which the image will
be rendered and cropped and *thumb_size* which are the dimensions to
which the rendered screenshot will be resized to. By default those
values are '1280x1024' and '320x200', respectively.

# Current flaws #

Obviously, the service in its current form is a gigantic forkbomb :)
One can easily fire off enough requests  to kill it, as Tornado will
do a pretty good job of spawning things until the system blocks. If
you are running thumbsup behind a reverse proxy of some sort, I would
strongly advise you to make good use of its rate-limiting. Most of
them have some sort of rate-limiting mechanism. 

You can keep a pretty large number of files, as long as you create a
good number of subfolders in your storage location, but you need to do
this manually and the service needs to be restarted.
