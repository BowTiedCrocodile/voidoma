#!/bin/sh
set -eu
cd -- "$(dirname -- "$0")"
mkdir -p sources
for repo in python-validity open-fprintd; do
    if [ ! -d "sources/$repo/.git" ]; then
        git clone "https://github.com/uunicorn/$repo.git" "sources/$repo"
    fi
done
git -C sources/python-validity checkout --detach a6bbc21dce7b8b3c3cd92378a0b2579a2fb45920
git -C sources/open-fprintd checkout --detach b7073730bccca36e84484e3fcb4f8253ea038d07
