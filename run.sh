#! /usr/bin/env bash
declare -a action
action=("${@:-preview}")
quarto "${action[@]}"
