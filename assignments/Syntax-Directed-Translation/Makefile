CC ?= cc
BISON ?= bison
CFLAGS ?= -O2 -g -std=c17 -Wall -Wextra -Wpedantic
CPPFLAGS += -D_POSIX_C_SOURCE=200809L -Iinclude -Ibuild
LDLIBS += -lm

objects := $(addprefix build/,common.o graph.o lr.o main.o mini.o parser.o check.o)

all: build/assignment3

build:
	mkdir -p $@

build/parser.c: grammar/parser.y include/lr.h include/common.h | build
	$(BISON) -d -o $@ $<

build/parser.h: build/parser.c
	test -f $@ || $(BISON) -d -o build/parser.c grammar/parser.y

build/%.o: src/%.c | build
	$(CC) $(CPPFLAGS) $(CFLAGS) -MMD -MP -c $< -o $@

build/check.o: tests/check.c | build
	$(CC) $(CPPFLAGS) $(CFLAGS) -MMD -MP -c $< -o $@

build/parser.o: build/parser.c build/parser.h
	$(CC) $(CPPFLAGS) $(CFLAGS) -MMD -MP -c $< -o $@

build/lr.o: build/parser.h

build/assignment3: $(objects)
	$(CC) $(CFLAGS) $(LDFLAGS) $^ $(LDLIBS) -o $@

check: build/assignment3
	mkdir -p evidence
	./build/assignment3 check

clean:
	rm -rf build

-include $(objects:.o=.d)
.PHONY: all check clean
