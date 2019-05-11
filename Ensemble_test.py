from EPICS_motor import motor
SampleX = motor("14IDB:SAMPLEX")
SampleY = motor("14IDB:SAMPLEY")
SampleZ = motor("14IDB:SAMPLEZ")
SamplePhi = motor("14IDB:SAMPLEPHI")

from time import sleep

while True:
  SampleX.value,SampleY.value,SampleZ.value = -1,-1,-1
  while(SampleX.moving or SampleY.moving or SampleZ.moving): sleep(0.01)
  sleep(1)
  SampleX.value,SampleY.value,SampleZ.value = 1,1,1
  while(SampleX.moving or SampleY.moving or SampleZ.moving): sleep(0.01)
  sleep(1)
