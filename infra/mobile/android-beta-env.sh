#!/bin/sh
# Source this file before running the local Android beta build on this Mac.
export JAVA_HOME="$HOME/Library/Java/JavaVirtualMachines/la-lanh-temurin21.jdk/Contents/Home"
export ANDROID_HOME="$HOME/Library/Android/sdk"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
export PATH="$JAVA_HOME/bin:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$PATH"
