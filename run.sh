#! /usr/bin/env nix-shell
#! nix-shell -i bash -p quarto python3Packages.jupyter texliveFull


./server.py &
server_pid=$!

trap "kill $server_pid" EXIT
# Race condition if quarto starts up before server
sleep 0.5

action=${@:-"preview"}
quarto $action
