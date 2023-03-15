
#!/bin/bash

say() {
    echo "HELLO"
}

build() {
    echo "Current environment is: $CONDA_DEFAULT_ENV"

    echo "Installate dependencies ..."

    conda install --file requirements.txt

    echo "Clone LTB packages ..."

    git clone https://github.com/CURENT/ltb.git --recursive

    echo "Install LTB DiME ..."
    cd $HOME/hlcosim/ltb/dime/server
    make
    make install

    echo "Initialize LTB ANDES ..."
    cd $HOME/hlcosim
    andes prep

    if [ -f $HOME/.andes/andes.rc ]; then rm $HOME/.andes/andes.rc; fi
    cp $HOME/hlcosim/code/andes.rc $HOME/.andes/
    echo "Removed default andes config and set the given config."
}

clean() {
    echo "Current environment is: $CONDA_DEFAULT_ENV"

    echo "Remove LTB packages ..."
    if [ -d $HOME/hlcosim/ltb/ ]; then rm -rf $HOME/hlcosim/ltb; fi

    echo "Remove LTB DiME file ..."
    if [ -f tmp/dime2 ]; then rm tmp/dime2; fi
}

sweb() {
    echo "Start the web ..."
    python3 -m http.server -d ./static 8810 --bind 0.0.0.0
}

sdime() {
    dime -l unix:/tmp/dime2 -l unix:/var/run/dime.sock -l ws:8818 -vv
}

sjupyter() {
    sudo -E env "PATH=$PATH" jupyter notebook --allow-root
}