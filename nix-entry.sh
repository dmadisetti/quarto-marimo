#! /usr/bin/env nix-shell
#! nix-shell -i bash -p quarto python3Packages.jupyter texliveFull
SERVER_SCRIPT=./server.py ./run.sh $@
