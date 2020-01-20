# Makefile to assist developers while modifying and testing changes before release
# Note: to re-install a release of EV3DEV2, use `sudo apt-get --reinstall install python3-ev3dev2`
OUT := build
MPYCROSS := /usr/bin/mpy-cross
MPYC_FLAGS := -v -v -mcache-lookup-bc
PYS := $(shell find ./ev3dev2 -type f \( -iname "*.py" ! -iname "setup.py" \))
MPYS := $(PYS:./%.py=${OUT}/%.mpy)
vpath %.py .

${OUT}/%.mpy: %.py
	@mkdir -p $(dir $@)
	${MPYCROSS} ${MPYC_FLAGS} -o $@ $<

install:
	python3 setup.py install

micropython-install: ${MPYS}
	cp -R $(OUT)/* /usr/lib/micropython/

clean:
	find . -name __pycache__ | xargs rm -rf
	find . -name *.pyc | xargs rm -rf

format:
	yapf --style .yapf.cfg --in-place --exclude tests/fake-sys/ --recursive .
