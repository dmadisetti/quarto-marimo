#! /usr/bin/env nix-shell
#! nix-shell -i bash -p quarto python3Packages.jupyter


./server.py &
server_pid=$!

trap "kill $server_pid" EXIT

action=${1:-"preview"}
quarto $action
