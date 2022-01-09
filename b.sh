#!/bin/bash -e

CFLAGS=$(pkg-config --cflags gtk4)

for i in $(find out -name *.cpp); do
    echo "Building $i"
    g++ -c -std=c++20 -I. -Iout $CFLAGS -o ${i/cpp/o} $i
done
