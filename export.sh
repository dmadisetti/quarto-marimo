#! /usr/bin/env bash


TUTORIALS=$(python -c "print(__import__('marimo').__path__.pop())")

for py in "$TUTORIALS"/_tutorials/*.py; do
  if [[ $py != *_tutorials/_* ]]; then
    python ./convert.py "$py" > "tutorials/$(basename "$py" .py).qmd"
  fi
done
