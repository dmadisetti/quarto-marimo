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
    marimo export md "$py" > "$(basename "$py" .py).qmd"
  fi
done

for md in "$TUTORIALS"/_tutorials/*.md; do
  # Somehow the literal *.md can be globbed.
  if [ "$md" == '*.md' ] || [ $(basename "$md") == "README.md" ]; then
    continue
  fi
  # ignore hidden cases
  if [[ $md != *_tutorials/_* ]]; then
    echo $md
    cp "$md" "$(basename "$md" .md).qmd"
  fi
done

cd -
