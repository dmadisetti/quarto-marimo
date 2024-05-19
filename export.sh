#! /usr/bin/env bash


TUTORIALS=$(python -c "print(__import__('marimo').__path__.pop())")

cd "$(dirname "$0")"/tutorials

for py in "$TUTORIALS"/_tutorials/*.py; do
  # Somehow the literal *.py can be globbed.
  if [ "$py" == '*.py' ]; then
    continue
  fi
  # ignore hidden cases
  if [[ $py != *_tutorials/_* ]]; then
    echo $py
    marimo export md "$py" > "$(basename "$py" .py).md"
  fi
done

cd -
