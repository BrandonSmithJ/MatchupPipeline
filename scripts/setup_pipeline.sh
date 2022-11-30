#!/bin/bash

USR=/discover/nobackup/$(whoami)
GIT=https://github.com
DST=Matchups

SHARED=/discover/nobackup/bsmith16/Matchups_Files

# Download URLs
PY3_URL="https://www.python.org/ftp/python/3.8.10/Python-3.8.10.tar.xz"
RMQ_URL="$GIT/rabbitmq/rabbitmq-server/releases/download/v3.10.10/rabbitmq-server-generic-unix-3.10.10.tar.xz"
ERL_URL="$GIT/erlang/otp/releases/download/OTP-25.1.2/otp_src_25.1.2.tar.gz"
FFI_URL="$GIT/libffi/libffi/releases/download/v3.4.4/libffi-3.4.4.tar.gz"
ACO_URL="$GIT/acolite/acolite/archive/refs/tags/20221114.0.tar.gz"


# Helper function
download_extract() {
    # Parameters:
    #    1: Destination folder
    #    2: URL for package (.tar.gz)
    #    
    # Download package from given url, and extract it.
    if [[ $# -lt 2 ]]; then
        echo "Too few arguments passed to download_extract:"
        echo "$@"
        exit 1
    fi

    mkdir -p $1 && cd $1
    wget $2 >/dev/null 2>&1
    local filename=$(ls *.tar.*)
    tar xf $filename >/dev/null 2>&1
    echo `pwd`/`tar -tf $filename | head -1 | cut -f1 -d"/"`
    rm $filename
    cd - > /dev/null
}


build_package() {
    # Parameters:
    #    1: Package folder
    #   2-: 
    #    
    # Build a package
    cd $1
    mkdir -p build
    ./configure --prefix=`pwd`/build
    make -j4 
    make install
    cd - > /dev/null
}


color_text() {
    # Parameters:
    #    1: Text to echo
    # 
    # Echo text with Cyan coloring
    COLOR='\033[0;36m'
    END='\033[0m'
    printf "${COLOR}${1}${END}\n"
}


scroll() {
    # Create a scrolling window of 10 lines of text for a command
    # Credit: https://unix.stackexchange.com/a/111528

    # save tty settings
    saved_stty=$(stty -g)

    restore()
    {
      stty $saved_stty
      # reset scrolling region
      printf "\033[1;${rows}r"

      # move to bottom of display
      printf "\033[999;1H"
    }

    trap restore int term exit

    # move to bottom of display
    printf "\033[999;1H"
    printf "\n\n\n\n\n\n\n\n\n"

    # Query the actual cursor position
    printf "\033[6n"

    # read tty response
    tty_response=
    stty raw isig -echo
    while true; do
        char=$(dd bs=1 count=1 2> /dev/null)
        if [ "$char" = "R" ] ; then
            break;
        fi
        tty_response="$tty_response$char"
    done
    stty $saved_stty

    # parse tty_response
    get_size()
    {
       cols=$3
       rows=$2
    }
    
    save_IFS=$IFS
    IFS='[;R'
    get_size $tty_response
    IFS=$save_IFS

    # set scrolling region to 10 lines
    printf "\033[$((rows-9));${rows}r"

    # move to bottom of display
    printf "\033[999;1H"

    # run command
    "$@"
    restore
    echo
}

# ----------------------------------

# Exit if any line fails
set -e

# Create symbolic link shortcut in the home directory
[ -e ~/storage ] || ln -s $USR ~/storage
cd ~/storage
mkdir -p $DST && cd $DST

# Clone the Matchup Pipeline
color_text "Cloning Matchup Pipeline"
color_text "------------------------"
scroll git clone https://github.com/BrandonSmithJ/MatchupPipeline pipeline
cp -R $SHARED/credentials pipeline/

# Install RabbitMQ
RMQ_PATH=$(download_extract RabbitMQ $RMQ_URL)

# Install Erlang
color_text "Installing Erlang"
color_text "-----------------"
ERL_PATH=$(download_extract RabbitMQ $ERL_URL)
scroll build_package $ERL_PATH

# Install libffi
color_text "Installing libffi"
color_text "-----------------"
FFI_PATH=$(download_extract Python $FFI_URL)
scroll build_package $FFI_PATH

# Install Python
color_text "Installing Python"
color_text "-----------------"
FFI=$FFI_PATH/build
export LDFLAGS="-L$FFI/lib64 -L$FFI/lib/pkgconfig -Wl,-rpath,$FFI/lib/pkgconfig -Wl,-rpath,$FFI/lib64" 
export CPPFLAGS="-I$FFI/include"
PY3_PATH=$(download_extract Python $PY3_URL)
scroll build_package $PY3_PATH

# Create virtual environment
color_text "Creating virtual environment"
color_text "----------------------------"
$PY3_PATH/build/bin/python3 -m venv venv
source venv/bin/activate
module load gdal/3.0.4

# Remove landsatxplore dependency, as it conflicts with others
# Manually install landsatxplore, and reinstall correct click version
install_reqs() {
  sed -i '/landsatxplore/d' pipeline/requirements.txt
  python -m pip install -r pipeline/requirements.txt && \
  python -m pip install landsatxplore && \
  python -m pip install click==8.1.3
}
scroll install_reqs

# Install Acolite
color_text "Installing Atmospheric Correction Processors"
color_text "--------------------------------------------"
ACO_PATH=$(download_extract AC/Acolite $ACO_URL)

# Install SeaDAS
mkdir -p AC/SeaDAS && cd AC/SeaDAS
wget https://oceandata.sci.gsfc.nasa.gov/manifest/install_ocssw >/dev/null 2>&1
wget https://oceandata.sci.gsfc.nasa.gov/manifest/manifest.py >/dev/null 2>&1
chmod +x install_ocssw
scroll ./install_ocssw --install_dir=`pwd` --tag T2022.31 --seadas --oli --l5tm --l7etmp --msis2a --msis2b


# Add RabbitMQ start script to the RabbitMQ folder, and run it
cp pipeline/scripts/start_rabbitmq.sh RabbitMQ/
cd RabbitMQ && ./start_rabbitmq.sh

# Add environmental variables to bashrc
echo "export SCREENDIR=$USR/.screens" >> ~/.bashrc
echo "export PATH=$ERL_PATH/build/bin:\$PATH" >> ~/.bashrc
echo "module load gdal/3.0.4" >> ~/.bashrc

echo
echo 'Run "source ~/.bashrc" to finalize all updates'
