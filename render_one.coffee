page = require('webpage').create()
system = require 'system'

[url, dst, width, height, ua] = system.args[1..]

page.userAgent = ua
page.viewportSize = {width: width, height: height}
page.clipRect = { top: 0, left: 0, width: width, height: height }

# Warning, output before the processing is done will currently BLOCK in the handler
# console.log("DEBUG: Attempting to fetch #{ url }")

page.open url, (status) ->
    if status is 'success'
        page.render dst
        console.log("INFO: Saved #{ url } screenshot as #{ dst }")
        phantom.exit(0)
    else
        console.log('ERROR: Unable to load the address!')
        phantom.exit(1)
