#!/bin/sh
set -ex

if [ -e ~/micropython/ports/unix/micropython ]; then
    # the micropython binary already exists, which means that the cached folder was restored
    exit 0
fi

cd ~/

# Build micropython from source
# TODO: cache micropython build output
git clone --recurse-submodules https://github.com/micropython/micropython.git --depth 1 --branch v1.9.4 --quiet
cd ./micropython/ports/unix
make axtls
make

# Install upip
~/micropython/tools/bootstrap_upip.sh

# Install micropython library modules
~/micropython/ports/unix/micropython -m upip install micropython-unittest micropython-os micropython-os.path micropython-shutil micropython-io micropython-fnmatch micropython-numbers micropython-struct micropython-time micropython-logging micropython-select
# Make unittest module show error output; will run until failure then print first error
# See https://github.com/micropython/micropython-lib/blob/f20d89c6aad9443a696561ca2a01f7ef0c8fb302/unittest/unittest.py#L203
sed -i 's/#raise/raise/g' ~/.micropython/lib/unittest.py