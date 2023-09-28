#!/bin/bash

set -x

if [ ! $VIRTUAL_ENV ]; then
 echo "${bold}${red}Can't install outside of a Python virtualenv${normal}"; exit 1
fi

bold=$(tput bold)
normal=$(tput sgr0)
red=$(tput setaf 160)

j=1

while (( $# >= 1 )); do
    case $1 in
    -j) j=$2; shift; shift;;
    --no-gigahorse) NO_GIGAHORSE=TRUE; shift; shift;;
    *) break;
    esac;
done

# navigate to this script's directory
GREED_DIR=`dirname "${BASH_SOURCE[0]}"`
GREED_DIR=`readlink -f $GREED_DIR` || { echo "${bold}${red}Can't find greed absolute path ${normal}"; exit 1; }
GIGAHORSE_DIR=$GREED_DIR/gigahorse-toolchain

VIRTUAL_ENV_BIN=$VIRTUAL_ENV/bin
VIRTUAL_ENV_LIB=`echo $VIRTUAL_ENV/lib/python3.*/site-packages`

########################################################################################################################
########################################################################################################################
# YICES
########################################################################################################################

# # clone the yices2 repo
# if [ ! -d $GREED_DIR/yices2 ]; then
#   git clone https://github.com/SRI-CSL/yices2.git $GREED_DIR/yices2
# fi

# cd $GREED_DIR/yices2

# # check if all required packages are installed (cmake, cython, libgmp-dev)
# dpkg -l | grep -q gcc || { echo "${bold}${red}gcc is not installed. Please install it before proceeding (e.g., sudo apt install gcc)${normal}"; exit 1; }
# dpkg -l | grep -q cmake || { echo "${bold}${red}cmake is not installed. Please install it before proceeding (e.g., sudo apt install cmake)${normal}"; exit 1; }
# dpkg -l | grep -q gperf || { echo "${bold}${red}gperf is not installed. Please install it before proceeding (e.g., sudo apt install gperf)${normal}"; exit 1; }
# dpkg -l | grep -q libgmp-dev || { echo "${bold}${red}libgmp-dev is not installed. Please install it before proceeding (e.g., sudo apt install libgmp-dev)${normal}"; exit 1; }

# # install
# make clean || { echo "${bold}${red}Failed to run make clean ${normal}. Continuing..."; }
# autoconf || { echo "${bold}${red}Failed to run autoconf${normal}"; exit 1; }
# ./configure || { echo "${bold}${red}Failed to run ./configure${normal}"; exit 1; }
# make || { echo "${bold}${red}Failed to run make${normal}"; exit 1; }

# # finally, link yices2/build/lib/ to the virtualenv's site-packages dir
# ln -sf $GREED_DIR/yices2/build/*-release/bin/* $VIRTUAL_ENV_BIN/
# ln -sf $GREED_DIR/yices2/build/*-release/lib/* $VIRTUAL_ENV_LIB/
# cp $VIRTUAL_ENV/lib/python3.*/site-packages/libyices.so.* $VIRTUAL_ENV_LIB/libyices.so

cd $GREED_DIR

# clone the yices2_python_bindings repo
if [ ! -d $GREED_DIR/yices2_python_bindings ]; then
  git clone https://github.com/ruaronicola/yices2_python_bindings.git $GREED_DIR/yices2_python_bindings
fi

# for some reason github builds fail to find libyices.so. This should fix it
python -c "import sys; print(sys.path)"
export PYTHONPATH=$PYTHONPATH:$VIRTUAL_ENV_LIB
python -c "import sys; print(sys.path)"
cp $GREED_DIR/resources/yices_api.py yices2_python_bindings/yices_api.py
cp $GREED_DIR/resources/setup.py yices2_python_bindings/setup.py
which python
which pip
python --version
python -m site
pip --version
pip freeze --all
pip install -v -e yices2_python_bindings
yices_python_info
cat /tmp/syspath0
cat /tmp/syspath

########################################################################################################################
########################################################################################################################
# GIGAHORSE
########################################################################################################################

if [ -z $NO_GIGAHORSE ]; then
  # install solc-select
  command -v >&- mkisofs || echo "${bold}${red}mkisofs is not installed. solc-select might not work correctly (e.g., sudo apt install mkisofs)${normal}"
  solc-select versions | grep -q 0.8.7 || { echo "Installing solc 0.8.7"; solc-select install 0.8.7; }

  # then install gigahorse from the official repo
  echo "Number of parallel datalog jobs: $j (override with $0 -j N)"
  read -rsn1 -p "Setting up gigahorse.. Press any key to continue (ctrl-c to abort)"
  echo

  command -v >&- souffle || { echo "${bold}${red}souffle is not installed. Please install it before proceeding (see https://github.com/souffle-lang/souffle/releases/tag/2.4 and https://souffle-lang.github.io/build, version 2.4 preferred)${normal}"; echo "${bold}${red}Or maybe you forgot --no-gigahorse?${normal}"; exit 1; }
  dpkg -l | grep -q libboost-all-dev || { echo "${bold}${red}libboost-all-dev is not installed. Please install it before proceeding (e.g., sudo apt install libboost-all-dev)${normal}"; echo "${bold}${red}Or maybe you forgot --no-gigahorse?${normal}"; exit 1; }

  # clone the gigahorse-toolchain repo
  if [ ! -d $GREED_DIR/gigahorse-toolchain ]; then
    git clone --recursive https://github.com/nevillegrech/gigahorse-toolchain.git $GIGAHORSE_DIR
    cd $GIGAHORSE_DIR
    git checkout c5bce4d3495fc10f503b49368504efee3c676d03
  fi

  # copy greed client
  cp $GREED_DIR/resources/greed_client.dl $GIGAHORSE_DIR/clientlib/

  # compile souffle
  echo "Compiling souffle-addon.."
  cd $GIGAHORSE_DIR/souffle-addon
  make || { echo "${bold}${red}Failed to build gigahorse's souffle-addon${normal}"; exit 1; }
  cd $GREED_DIR

  # compile gigahorse clients
  echo "Compiling gigahorse clients. This will take some time.."
  function compile () {
    echo "Compiling $1.."
    souffle --jobs $j -M "GIGAHORSE_DIR=$GIGAHORSE_DIR BULK_ANALYSIS=" -o $GIGAHORSE_DIR/clients/$1_compiled.tmp $GIGAHORSE_DIR/$2 -L $GIGAHORSE_DIR/souffle-addon || { echo "${bold}${red}Failed to build $1_compiled${normal}"; exit 1; } &&
    mv $GIGAHORSE_DIR/clients/$1_compiled.tmp $GIGAHORSE_DIR/clients/$1_compiled &&
    mv $GIGAHORSE_DIR/clients/$1_compiled.tmp.cpp $GIGAHORSE_DIR/clients/$1_compiled.cpp &&
    echo "Successfully compiled $1.."
  }
  compile "main.dl" "logic/main.dl"
  compile "greed_client.dl" "clientlib/greed_client.dl"
else
  true
fi

########################################################################################################################
########################################################################################################################
# GREED
########################################################################################################################

# link our scripts into virtualenv's bin dir
echo "Linking scripts into virtualenv's bin directory.."
for script in $GREED_DIR/resources/{*.sh,*.py}; do
  ln -sf $script $VIRTUAL_ENV_BIN/
done

# create alias for run.py
echo "Creating alias run.py -> greed.."
ln -sf $GREED_DIR/resources/run.py $VIRTUAL_ENV_BIN/greed

# install greed
pip install -e $GREED_DIR

########################################################################################################################

set +x
