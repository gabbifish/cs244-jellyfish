## Jellyfish Paper replication Readme

### Setup
This code has only been tested on Linux Debian 4.9, but should also work on latest versions of Ubuntu or Debian.

First, you must install mininet:
```
apt-get install mininet
```

Then, download pox in the same directory as mininet:
```
git clone https://github.com/noxrepo/pox
```

Ensure you have pip, the python package manager installed:
```
apt-get install pip
```

Copy the contents of this github repository into pox/ext.

Finally, run the following to download any final python dependencies:
```
pip install -r requirements.txt
```

### Generating Figure 9
Run
```
./count_link_paths.py
```
to generate Figure 9. Figure 9 will be in generated file figure9.png.

### Generating Data for Table 1
Run
```
./count_throughput_bandwidth
```
to run the mininet simulation and iperf experiments. This will generate Table 1 as output in table1_withbaseline.png.

### How to run Mininet Cli with Custom POX Controller
First, you will need to ensure screen is installed. You can use apt-get to install.

Then, launch POX with a custom controller jelly_controller.py; use screen to launch POX in a separate screen so you can still use the mininet cli. From the `~/pox/pox/cd` directory run:

```
pushd ../../ ; screen -dmS pox python pox.py ext.jelly_controller ; popd
```

POX will now run in a separate screen. You can access this screen using `screen -r pox`. To exit that screen, press `Ctrl-A D`.

Next, you must start the mininet client over your custom topology and configure it to use your custom POX controller. From the `~/pox/pox/cd` directory, run the following:

```
sudo mn --custom build_topology.py --topo JellyTopo --controller=remote,ip=127.0.0.1,port=6633
```

That starts a test on the custom mininet topology using your custom controller!

If you want to keep the mininet client open, do not specify a test. Run the `sudo mn` command above but remove the `--test` flag and its argument.

If you ever want to kill POX and the screen it's running on, you can simply switch to the POX screen and press `Ctrl-A`, then type `:quit`.
