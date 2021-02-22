# Onionr HTTP API

All HTTP interfaces in the Onionr reference client use the [Flask](http://flask.pocoo.org/) web framework with the [gevent](http://www.gevent.org/) WSGI server.

## Client & Public difference

The client API server is a locked down interface intended for authenticated local communication.

The public API server is available only remotely from Tor & I2P. It is the interface in which peers use to communicate with one another.

# Client API

Please note: endpoints that simply provide static web app files are not documented here.

* /serviceactive/pubkey
    - Methods: GET
    - Returns true or false based on if a given public key has an active direct connection service.
* /queueResponseAdd/key (DEPRECATED)
    - Methods: POST
    - Accepts form key 'data' to set queue response information from a plugin
    - Returns success if no error occurs
* /queueResponse/key (DEPRECATED)
    - Methods: GET
    - Returns the queue response for a key. Returns failure with a 404 code if a code is not set.
* /ping
    - Methods: GET
    - Returns "pong!"
* /getblocksbytype/type
    - Methods: GET
    - Returns a list of stored blocks by a given type
* /getblockbody/hash
    - Methods: GET
    - Returns the main data section of a block
* /getblockdata/hash
    - Methods: GET
    - Returns the entire data contents of a block, including metadata.
* /getblockheader/hash
    - Methods: GET
    - Returns the header (metadata section) of a block.
* /gethidden/
    - Methods: GET
    - Returns line separated list of hidden blocks
* /hitcount
    - Methods: GET
    - Return the amount of requests the public api server has received this session
* /lastconnect
    - Methods: GET
    - Returns the epoch timestamp of when the last incoming connection to the public API server was logged
* /site/hash
    - Methods: GET
    - Returns HTML content out of a block
* /waitforshare/hash
    - Methods: POST
    - Prevents the public API server from listing or sharing a block until it has been uploaded to at least 1 peer.
* /shutdown
    - Methods: GET
    - Shutdown Onionr. You should probably use /shutdownclean instead.
* /shutdownclean
    - Methods: GET
    - Tells the communicator daemon to shutdown Onionr. Slower but cleaner.
* /getstats
    - Methods: GET
    - Returns some JSON serialized statistics
* /getuptime
    - Methods: GET
    - Returns uptime in seconds

# Public API

v0

* /
    - Methods: GET
    - Returns a basic HTML informational banner describing Onionr.
* /getblocklist
    - Methods: GET
    - URI Parameters:
        - date: unix epoch timestamp for offset
    - Returns a list of block hashes stored on the node since an offset (all blocks if no timestamp is specified)
* /getdata/block-hash
    - Methods: GET
    - Returns data for a block based on a provided hash
* /www/file-path
    - Methods: GET
    - Returns file data. Intended for manually sharing file data directly from an Onionr node.
* /ping
    - Methods: GET
    - Returns 'pong!'
* /pex
    - Methods: GET
    - Returns a list of peer addresses reached within recent time
* /announce
    - Methods: POST
    - Accepts form data for 'node' (valid node address) and 'random' which is a nonce when hashed (blake2b_256) in the format `hash(peerAddress+serverAddress+nonce)`, begins with at least 5 zeros.
    - Returns 200 with 'Success' if no error occurs. If the post is invalid, 'failure' with code 406 is returned.
* /upload
    - Methods: POST
    - Accepts form data for 'block' as a 'file' upload.
    - Returns 200 with 'success' if no error occurs. If the block cannot be accepted, 'failure' with 400 is returned.

# Direct Connection API

These are constant endpoints available on direct connection servers. Plugin endpoints for direct connections are not documented here.

* /ping
    - Methods: GET
    - Returns 200 with 'pong!'

* /close
    - Methods: GET
    - Kills the direct connection server, destroying the onion address.
    - Returns 200 with 'goodbye'