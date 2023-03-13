System requirement: Windows WSL

Activate the environment for cosim:

```
conda activate hlc
```

Install DiME dependencies:

```
sudo apt-get install libssl-dev zlib1g-dev libjansson-dev
```

Clone Dime:

```
https://github.com/CURENT/dime.git
```

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

