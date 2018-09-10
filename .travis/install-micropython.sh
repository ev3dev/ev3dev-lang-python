#!/bin/sh
set -ex
cd ~/
git clone --recurse-submodules https://github.com/micropython/micropython.git --depth 1
cd ./micropython/ports/unix
make axtls
make
