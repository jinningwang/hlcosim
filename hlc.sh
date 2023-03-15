
[ -f env.sh ] && . env.sh

build{

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
andes prep -f

if [ -f $HOME/.andes/andes.rc ]; then rm $HOME/.andes/andes.rc; fi
cp $HOME/hlcosim/ltb/andes.rc $HOME/.andes/
echo "Removed default andes config and set the given config."

}
