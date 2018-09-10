#!/bin/sh
set -ex

cd ~/

# Build micropython from source
# TODO: cache build output
git clone --recurse-submodules https://github.com/micropython/micropython.git --depth 1 --branch v1.9.4
cd ./micropython/ports/unix
make axtls
make

# Install upip
~/micropython/tools/bootstrap_upip.sh

# Install dependencies
# TODO: make unittest show output
~/micropython/ports/unix/micropython -m upip install micropython-unittest micropython-os micropython-os.path micropython-shutil micropython-io micropython-fnmatch micropython-numbers micropython-struct micropython-time micropython-logging micropython-select