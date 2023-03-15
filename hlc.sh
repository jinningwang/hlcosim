
if [ -f $HOME/.andes/andes.rc ]; then rm $HOME/.andes/andes.rc; fi

cp `pwd`/ltb/andes.rc $HOME/.andes/

echo "Removed default andes config and set the given config."
