## Jellyfish Paper replication Readme

### How to run Mininet with Custom POX Controller
First, you will need to ensure screen is installed. You can use apt-get to install.

Then, launch POX with a custom controller jelly_controller.py; use screen to launch POX in a separate screen so you can still use the mininet cli. From the `~/pox` directory run:

```
screen -dmS pox python pox.py ext.jelly_controller
```

POX will now run in a separate screen. You can access this screen using `screen -r pox`. To exit that screen, press `Ctrl-A D`.

Next, you must start the mininet client over your custom topology and configure it to use your custom POX controller. From the `~/pox` directory, run the following:

```
cd pox/ext/
sudo mn --custom build_topology.py --topo JellyTopo --test pingall --controller=remote,ip=127.0.0.1,port=6633
```

That starts a test on the custom mininet topology using your custom controller!