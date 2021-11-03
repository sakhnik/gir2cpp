#!/bin/bash -e

cat >|compile_flags.txt <<END
-std=c++20
-Iout
$(pkg-config --cflags gtk4 | sed 's/ -/\n-/g')
END
