# CS305 Project: SDN

#### Introduction

This is the repository of SUSTech CS305 project. 
We do not use ANY open source license.
Please DO NOT use code in this repository in your project / assignment.  

#### Contributor

BoTian Xu
Wenhao Zhang
Mingji Han

#### Prerequsite

Ubuntu 16.04

#### Preparation

Install libraries

```
sudo apt-get install mininet python3-ryu iputils-arping
```


#### Run Our Program
Run `ryu-manager`
```
ryu-manager --observe-links shortest_paths.py

```
Run `mininet`

```
sudo python run_mininet.py single 3
```
Test our program

```
mininet > pingall
```
