#!/bin/bash -e

cat >|compile_flags.txt <<END
-std=c++20
-I.
-Iout
-Wno-deprecated
-Wno-deprecated-declarations
$(pkg-config --cflags gtk4 | sed 's/ -/\n-/g')
END
