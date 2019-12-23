# CS305 Project: SDN

#### Introduction

This is the repository of SUSTech CS305 project.  
Please DO NOT USE ANY code in this repository for your project / assignment.  

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
