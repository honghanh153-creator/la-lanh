UNAME_S := $(shell uname -s)
CC ?= cc
CFLAGS ?= -O2 -fPIC
SRC_DIR := src
BUILD_DIR := build
SOURCES := swedate.c swehouse.c swejpl.c swemmoon.c swemplan.c sweph.c swephlib.c swecl.c swehel.c
OBJECTS := $(SOURCES:%.c=$(BUILD_DIR)/%.o)

ifeq ($(UNAME_S),Darwin)
  LIBRARY := $(BUILD_DIR)/libswe.dylib
  SHARED_FLAGS := -dynamiclib
  SYSTEM_LIBS := -lm
else
  LIBRARY := $(BUILD_DIR)/libswe.so
  SHARED_FLAGS := -shared
  SYSTEM_LIBS := -lm -ldl
endif

.PHONY: all clean verify

all: $(LIBRARY)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(BUILD_DIR)/%.o: $(SRC_DIR)/%.c | $(BUILD_DIR)
	$(CC) $(CFLAGS) -I$(SRC_DIR) -c $< -o $@

$(LIBRARY): $(OBJECTS)
	$(CC) $(SHARED_FLAGS) -o $@ $(OBJECTS) $(SYSTEM_LIBS)

verify: $(LIBRARY)
	test -s $(LIBRARY)

clean:
	rm -rf $(BUILD_DIR)
