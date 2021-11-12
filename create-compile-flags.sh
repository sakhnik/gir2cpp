#!/bin/bash -e

cat >|compile_flags.txt <<END
-std=c++20
-Iout
-Wno-deprecated
$(pkg-config --cflags gtk4 | sed 's/ -/\n-/g')
END
