CC=gcc
CFLAGS=-c -Wall -g
LDFLAGS=

DEBUG_SETTINGS=-DCOLORFUL -DDEBUG_LEXER -DDEBUG_PARSER
RELEASE_SETTINGS=
SETTINGS=$(RELEASE_SETTINGS)

SOURCES=$(sort $(wildcard *.c) $(BISON_OUTPUT_C) $(FLEX_OUTPUT))
OBJECTS=$(SOURCES:.c=.o)
EXECUTABLE=eiffelp

FLEX_FILE=eiffel.flex
FLEX_OUTPUT=lex.yy.c

BISON_FILE=eiffel.y
BISON_OUTPUT_C=eiffel.tab.c
BISON_OUTPUT_H=eiffel.tab.h
BISON_OUTPUT=eiffel.output

.PHONY: debug
debug:
	$(MAKE) build SETTINGS="$(DEBUG_SETTINGS)"

.PHONY: build
build: clean bison flex $(SOURCES) $(EXECUTABLE)

.PHONY: bison
bison: $(BISON_FILE)
	bison --verbose -Wcounterexamples -d $<
	$(CC) $(CFLAGS) $(SETTINGS) $(BISON_OUTPUT_C) -o $(BISON_OUTPUT_C:.c=.o)

.PHONY: flex
flex: $(FLEX_FILE)
	flex $<
	$(CC) $(CFLAGS) $(SETTINGS) $(FLEX_OUTPUT) -o $(FLEX_OUTPUT:.c=.o)

$(EXECUTABLE): $(OBJECTS) 
	$(CC) -g $(LDFLAGS) $(OBJECTS) -o $@

.c.o:
	$(CC) $(CFLAGS) $(SETTINGS) $< -o $@

.PHONY: clean
clean:
	rm -rf $(OBJECTS) $(EXECUTABLE) $(FLEX_OUTPUT) $(BISON_OUTPUT_H) $(BISON_OUTPUT_C) $(BISON_OUTPUT)
