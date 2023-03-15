# Procedures

Recommended operating system: Windows WSL with Ubuntu 20.04 LTS

## Basic

Create a environment:
```
conda create --name hlc
```

Activate the environment:

```
conda activate hlc
```

Install dependencies:
```
conda install --file requirements.txt
```

## Visualization

Git clone the LTB packages:
```
git clone https://github.com/CURENT/ltb.git --recursive
```

### AGVis

```
cd ltb/agvis
```

Run the AGVis, and the web appilication should be available at localhost:8810
```
python3 -m http.server -d ./static 8810 --bind 0.0.0.0
```

### DiME

The dependecies should have been installed: OpenSSL, zlib, Jansson

Install DiME:
```
cd dime/server
```

```
make
```

```
make install
```

Run a DiME server:
```
sudo dime -l unix:/tmp/dime2 -l unix:/var/run/dime.sock -l ws:8818 -vv
```
Notes:
- Prefix ``sudo`` is used to give the root access
- Remember to activate the environment

### Jupyter notebook:

```
sudo -E env "PATH=$PATH" jupyter notebook --allow-root
```
Note:
- Run the jupyter notebook with root access
