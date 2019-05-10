#!/bin/bash
# Python Envronment for XPP Beamline
# Silke Nelson Jan 22, 2016
# Friedrich Schotte, Jan 22, 2016

source /reg/g/psdm/etc/ana_env.sh

export PSPKG_ROOT=/reg/common/package
source /reg/g/pcds/setup/pathmunge.sh
source $PSPKG_ROOT/etc/set_env.sh
export XPPFOLDER=/reg/g/pcds/pyps/xpp/prod/xpp
pythonpathmunge ${XPPFOLDER}
pythonpathmunge ${XPPFOLDER}/xpp
SETUPDIR="/reg/g/pcds/pyps/xpp/current/xpp"
source ${SETUPDIR}/xppenv.sh
