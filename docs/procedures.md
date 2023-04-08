## HTB-LTB Co-Simulation Operational Procedures

The LTB part is running in WSL, and the communication is done by file IO on disk.

You can use the LTB ANDES only for co-simulation, and you can also start all LTB modules for simulation and geo-visualization.

### LTB ANDES

In an Unix-likke terminal, change the path to the co-sim path

```
cd $HOME:\hlcosim\
```

Activate the HLC environment

```
conda activate hlc
```

Open Jupyter Notebook

```
jupyter notebook
```

To start the co-simulation, start the LTB first.

### LTB DiME

In an Unix-likke terminal, change the path to the LTB DiME server path

```
cd $HOME:\hlcosim\ltb\dime\server
```

Start a DiME server

```
dime -l unix:/tmp/dime2 -l unix:/var/run/dime.sock -l ws:8818 -vv
```

### LTB AGVis

In an Unix-likke terminal, change the path to the AGVis path

```
cd $HOME:\hlcosim\ltb\agvis
```

Start the AGVis

```
python3 -m http.server -d ./static 8810 --bind 0.0.0.0
```
