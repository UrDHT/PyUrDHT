PyUrDHT
========

This project is part of the URDHT project to simplify and generalize DHTs.
The ultimate goal is to create a solid, accessible, and powerful backend for p2p applications.
Using the Client libraries, ideally developers should be able to use the Decentralized P2P DHT as a database and messaging layer for building their own applications.

Right now PyUrDHT is still in early development, and should be treated as such (expect bugs! Please report them in our issue tracker!). If you are interested in running a node to support the alpha testnet, read on:

## Installation

Ideally, PyUrDHT depends only on an install of Python 3.4+.
Libraries this project depends on have been incorporated into this repository.

- Clone this repository
- Edit config.json to match your network configuration
- run python3 main.py to start the server (use 'screen' to run in the background right now)

## Configuring config.json

config.json looks like this:

```
{
	"bindAddr":"0.0.0.0",
	"bindPort":8000,
	"bootstraps":"bootstrap.json",
	"publicAddr":"",
	"loc":""
}

```

the "bindAddr" and "bindPort" indicate the network interface and port you want to bind to.
"publicAddr" is a url where your server can be reached, it should use your public ip and port utilized by NAT or port forwarding. You can use DNS names if they are configured to reach your node.
