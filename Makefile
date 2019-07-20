OUT := build
MPYCROSS := /usr/bin/mpy-cross
MPYC_FLAGS := -v -v -mcache-lookup-bc
PYS := $(shell find ./ev3dev2 -type f \( -iname "*.py" ! -iname "setup.py" \))
MPYS := $(PYS:./%.py=${OUT}/%.mpy)
vpath %.py .

${OUT}/%.mpy: %.py
	@mkdir -p $(dir $@)
	${MPYCROSS} ${MPYC_FLAGS} -o $@ $<

install: ${MPYS}
	cp -R $(OUT)/* /usr/lib/micropython/
