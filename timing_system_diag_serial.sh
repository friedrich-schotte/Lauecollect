#!/bin/bash
while [ true ] ; do
  telnet 14serial1.cars.aps.anl.gov 2001
  echo -e "\033[07m Hit Enter to reconnect \033[00m"
  read
done