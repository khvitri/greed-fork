#!/bin/bash -e

usage() {
  echo "usage: $(basename "$0") --dir <directory containing contract .hex> --timeout <timeout> --threads <#threads> --out <output directory>"
}

TIMEOUT=360
THREADS=7
OUTPUT_DIR="decompiled-contracts/"

while (($# >= 1)); do
  case $1 in
  --dir)
    HEX_DIR=$2
    shift
    shift
    ;;
  --timeout)
    TIMEOUT="${2}"
    shift
    shift
    ;;
  --threads)
    THREADS="${2}"
    shift
    shift
    ;;
  --out)
    OUTPUT_DIR="${2}"
    shift
    shift
    ;;
  *) break ;;
  esac
done

if [[ -z $HEX_DIR ]]; then
  usage
  exit 1
elif [ ! -d $HEX_DIR ]; then
  echo "$HEX_DIR is not a directory"
  usage
  exit 1
fi

FILEPATH=$(readlink -f "${BASH_SOURCE[0]}")
GREED_DIR=$(dirname $FILEPATH)
GREED_DIR=$(readlink -f $GREED_DIR/../)
GIGAHORSE_DIR=$GREED_DIR/gigahorse-toolchain

if [ ! -f $GIGAHORSE_DIR/clients/main.dl_compiled ]; then
  echo "Can't find main.dl_compiled (something went wrong in setup.sh)"
  exit 1
elif [ ! -f $GIGAHORSE_DIR/clients/greed_client.dl_compiled ]; then
  echo "Can't find greed_client.dl_compiled (something went wrong in setup.sh)"
  exit 1
fi

echo "Running gigahorse.py"
/usr/bin/time -v $GIGAHORSE_DIR/gigahorse.py -j "${THREADS}" -T $TIMEOUT --reuse_datalog_bin --disable_inline -C $GIGAHORSE_DIR/clients/greed_client.dl_compiled,$GIGAHORSE_DIR/clients/visualizeout.py $HEX_DIR |& tee -a exec_info &&
  curr_dir=$(pwd) && cd $GIGAHORSE_DIR && gigahorse_version=$(git rev-parse HEAD) && cd $curr_dir && printf "\tGigahorse version: $gigahorse_version\n" >>exec_info &&
  curr_dir=$(pwd) && cd $GREED_DIR && greed_version=$(git rev-parse HEAD) && cd $curr_dir && printf "\tgreed version: $greed_version\n" >>exec_info

for path in .temp/*; do
  [ -d $path ] || continue
  rm $path/out/bytecode.hex
  mv $path/out/* $path
  mv $path/bytecode.hex $path/contract.hex
  rm -rf $path/out $path/Analytics_ReachableUnderContext.csv $path/Analytics_Contexts.csv
  chmod 664 $path/*
done

mkdir -p "${OUTPUT_DIR}"
find .temp/ -maxdepth 1 -mindepth 1 -type d -exec basename -z {} \; | xargs -0 -I{} --max-procs "${THREADS}" bash -c "rm -rf ${OUTPUT_DIR}/{} && mv -t ${OUTPUT_DIR}/ .temp/{}"
rm -rf .temp
