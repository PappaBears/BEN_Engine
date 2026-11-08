# BEN Pod — host fallback build. Used when the PlatformIO `native` platform cannot be
# downloaded (network-restricted build hosts). Builds lib/bencore + the mock HAL with the
# system g++ and runs test/test_core against a Unity-compatible shim (test/support/unity.h).
#
#   make test      # build + run unit tests
#   make sim       # build src/main.cpp in native mode and run the 5 s simulation
#   make clean
CXX      ?= g++
CXXFLAGS ?= -std=c++17 -O1 -g -Wall -Wextra -Wno-unused-parameter \
            -DBEN_NATIVE -DBEN_FW_VERSION=\"1.0.0\" -DBEN_RING_SECONDS=3600 \
            -Ilib -Ilib/bencore -Ilib/benhal
BUILD    := .build-host
CORE_SRC := $(wildcard lib/bencore/*.cpp) $(wildcard lib/benhal/*.cpp)
CORE_OBJ := $(patsubst %.cpp,$(BUILD)/%.o,$(CORE_SRC))
TEST_SRC := $(wildcard test/test_core/*.cpp)
DEPS     := $(CORE_OBJ:.o=.d)

.PHONY: all test sim clean
all: test

$(BUILD)/%.o: %.cpp
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) -MMD -MP -c $< -o $@

$(BUILD)/test_core: $(CORE_OBJ) $(TEST_SRC)
	$(CXX) $(CXXFLAGS) -Itest/support $(TEST_SRC) $(CORE_OBJ) -o $@

$(BUILD)/node_sim: $(CORE_OBJ) src/main.cpp
	$(CXX) $(CXXFLAGS) src/main.cpp $(CORE_OBJ) -o $@

test: $(BUILD)/test_core
	./$(BUILD)/test_core

sim: $(BUILD)/node_sim
	./$(BUILD)/node_sim

clean:
	rm -rf $(BUILD)

-include $(DEPS)
