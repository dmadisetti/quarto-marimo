#! /usr/bin/env sh

# `nix run .#run` provides server as script
# so at least this is a bit more portable
server=${SERVER_SCRIPT:-python ./server.py}

# Start the server in the background
$server &
server_pid=$!
trap "kill $server_pid" EXIT

# Race condition if quarto starts up before server
sleep 0.5

action=${@:-"preview"}
quarto $action
