#!/bin/bash -e

CFLAGS=$(pkg-config --cflags gtk4)

for i in $(find out -name *.cpp); do
    echo "Building $i"
    g++ -c -std=c++20 -I. -Iout -Wno-deprecated -Wno-deprecated-declarations $CFLAGS -o ${i/cpp/o} $i
done
