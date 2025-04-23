#!/bin/bash

while (($# >= 1)); do
  case $1 in
  --dir)
    HEX_DIR=$2
    shift
    shift
    ;;
  --timeout)
    TIMEOUT=$2
    shift
    shift
    ;;
  *) break ;;
  esac
done

if [[ -z $HEX_DIR ]]; then
  echo usage: analyze_hex.sh --dir \<directory containing contract .hex\> --timeout \<timeout\>
  exit 1
elif [[ -z $TIMEOUT ]]; then
  TIMEOUT=3600 # Default timeout is 1 hour
#  echo usage: analyze_hex.sh --file \<contract .hex file\> --timeout \<timeout\>
#  exit 1
elif [ ! -d $HEX_DIR ]; then
  echo $HEX_DIR is not a file
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
/usr/bin/time -v $GIGAHORSE_DIR/gigahorse.py -j 8 -T $TIMEOUT --reuse_datalog_bin --disable_inline --rerun_clients -C $GIGAHORSE_DIR/clients/greed_client.dl_compiled,$GIGAHORSE_DIR/clients/visualizeout.py,$GIGAHORSE_DIR/clients/slicing.dl $HEX_DIR &>exec_info &&
  curr_dir=$(pwd) && cd $GIGAHORSE_DIR && gigahorse_version=$(git rev-parse HEAD) && cd $curr_dir && printf "\tGigahorse version: $gigahorse_version\n" >>exec_info &&
  curr_dir=$(pwd) && cd $GREED_DIR && greed_version=$(git rev-parse HEAD) && cd $curr_dir && printf "\tgreed version: $greed_version\n" >>exec_info

for path in .temp/*; do
  [ -d $path ] || continue
  rm $path/out/bytecode.hex
  cp $path/out/* $path
  mv $path/bytecode.hex $path/contract.hex
  rm -rf $path/out $path/Analytics_ReachableUnderContext.csv $path/Analytics_Contexts.csv
  chmod 664 $path/*
done

mv .temp/* .
rm -rf .temp
