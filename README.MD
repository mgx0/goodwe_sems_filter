# GoodWe SEMS TCP Proxy

A lightweight TCP proxy for GoodWe solar inverters that filters and forwards communications between your inverters and the GoodWe SEMS platform.

## Overview

This proxy sits between your GoodWe inverters and the official GoodWe SEMS platform (`tcp.goodwe-power.com`). It allows you to:

- Monitor data being sent from your inverters to GoodWe
- Optionally allow or block download communications from GoodWe to your inverters
- Log all traffic for debugging and analysis
- Run as a standalone service or in a container

## How It Works

```
GoodWe Inverter ↔ This Proxy ↔ GoodWe SEMS Platform
```

The proxy listens on TCP port 20001 (default GoodWe port) and forwards connections to the official GoodWe server. By default, it only allows data to flow from the inverter to the server (upload), but can be configured to allow bidirectional communication.

## Pre-requisite
You need to make sure the GoodWe WiFi/LAN Dongle resolves tcp.goodwe-power.com to your local IP, where this script is running. Use Google

## Configuration

The proxy is configured through environment variables:

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `ENABLE_DOWNLOAD` | Allow data from GoodWe to inverter | `False` | `True` |
| `DEBUG` | Enable verbose logging | `False` | `True` |


### Run Directly
This updates the repo, builds a docker image and starts it in background
```bash
./run.sh
```
