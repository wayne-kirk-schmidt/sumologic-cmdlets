#!/usr/bin/env ksh

umask 022

numdays=$1

numhours=$(( numdays * 24 ))

for (( i=numhours; i>=1; i-- ))
do
    j=$(( i - 1 ))
    echo "sumoquery -a API:KEY -q /path/to/query -e jp -t tky_SAMPLEORG -r ${i}h:${j}h"
done
