#!/bin/sh
# Downloads ACE 0.9.34 and the ERG 2018 image into ./erg/. Linux x86-64 only.
set -eu
base=http://sweaglesw.org/linguistics/ace/download
dir="$(cd "$(dirname "$0")/.." && pwd)/erg"
mkdir -p "$dir"
cd "$dir"
if [ ! -x ace ]; then
    curl -fL "$base/ace-0.9.34-x86-64.tar.gz" -o ace.tar.gz
    tar xzf ace.tar.gz
    mv ace-0.9.34/ace ace
    rm -r ace-0.9.34 ace.tar.gz
fi
if [ ! -f erg-2018.dat ]; then
    curl -fL "$base/erg-2018-x86-64-0.9.34.dat.bz2" -o erg-2018.dat.bz2
    bunzip2 erg-2018.dat.bz2
fi
./ace -V
ls -l erg-2018.dat
