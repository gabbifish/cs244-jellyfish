## Jellyfish Paper replication Readme

### How to run Mininet with Custom POX Controller
First, you will need to ensure screen is installed. You can use apt-get to install.

Then, launch POX with a custom controller jelly_controller.py; use screen to launch POX in a separate screen so you can still use the mininet cli. From the `~/pox/pox/cd` directory run:

```
pushd ../../ ; screen -dmS pox python pox.py ext.jelly_controller ; popd
```

POX will now run in a separate screen. You can access this screen using `screen -r pox`. To exit that screen, press `Ctrl-A D`.

Next, you must start the mininet client over your custom topology and configure it to use your custom POX controller. From the `~/pox/pox/cd` directory, run the following:

```
sudo mn --custom build_topology.py --topo JellyTopo --test pingall --controller=remote,ip=127.0.0.1,port=6633
```

That starts a test on the custom mininet topology using your custom controller!

If you want to keep the mininet client open, do not specify a test. Run the `sudo mn` command above but remove the `--test` flag and its argument.

If you ever want to kill POX and the screen it's running on, you can simply switch to the POX screen and press `Ctrl-A`, then type `:quit`.
