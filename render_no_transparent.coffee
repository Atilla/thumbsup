page = require('webpage').create()
system = require 'system'

[url, dst, width, height, ua, ip] = system.args[1..]

page.userAgent = ua
page.customHeaders =
        "X-Forwarded-For": ip
page.viewportSize =
    width: width
    height: height
page.clipRect =
    top: 0
    left: 0
    width: width
    height: height

# Warning, output before the processing is done will currently BLOCK in the handler
# console.log("DEBUG: Attempting to fetch #{ url }")

# Add a reaper timer, for anything long enough to be annoying
window.setTimeout (->
    console.log("ERROR: Timeout exceeded")
    phantom.exit(0)), 10000

page.open url, (status) ->
    if status is 'success'
        # Let's attempt to set BG color to white if it's transparent
        page_style = window.getComputedStyle(document.body, null)
        page_bg = page_style.backgroundColor.match(/\d+/g)
        if page_bg is null
            document.body.bgColor = 'white';
        page.render dst
        console.log("INFO: Saved #{ url } screenshot as #{ dst }")
        phantom.exit(0)
    else
        console.log('ERROR: Unable to load the address!')
        phantom.exit(1)
