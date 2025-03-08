PARSER_SOURCES=serpent/parser
EXECUTABLE=eiffelp
BUILD_DIR=serpent/resources/build

.PHONY: build
build: clean
	$(MAKE) -C $(PARSER_SOURCES) build
	mkdir -p ./$(BUILD_DIR)
	mv ./$(PARSER_SOURCES)/$(EXECUTABLE) ./$(BUILD_DIR)

.PHONY: debug
debug: clean
	$(MAKE) -C $(PARSER_SOURCES) debug
	mkdir -p ./$(BUILD_DIR)
	mv ./$(PARSER_SOURCES)/$(EXECUTABLE) ./$(BUILD_DIR)

.PHONY: clean
clean:
	rm -rf ./$(EXECUTABLE) ./$(BUILD_DIR)
	$(MAKE) -C $(PARSER_SOURCES) clean

.PHONY: test
test: $(BUILD_DIR)/$(EXECUTABLE)
	@pytest -v

# If the first argument is "view"...
ifeq (view,$(firstword $(MAKECMDGOALS)))
  # use the rest as arguments for "view"
  VIEW_ARGS = $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  # ...and turn them into do-nothing targets
  $(eval $(VIEW_ARGS):;@:)
endif

.PHONY: view
view: $(BUILD_DIR)/$(EXECUTABLE)
	@python ./test/visualize.py $(VIEW_ARGS)