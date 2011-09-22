#!/usr/bin/python
print('''
``
init-resources-py
Author: Andreas Hartel

This script creates symbolic links in ./resources 

´´
''')

import os
import sys
import subprocess


PATHS = ['/cad/libs/u18/FARADAY/fsa0a_c/2007Q1v1.3/T33_ANALOGESD_IO resources/fsa0a_c_t33_analogesd_io',
    '/cad/libs/u18/FARADAY/fsa0a_c/2005Q4v1.2/IO resources/fsa0a_c_io',
    '/cad/libs/u18/FARADAY/FXPLL031HA0A_APGD/2005Q3V1.3 resources/FXPLL031HA0A_APGD',
    '/cad/libs/u18/FARADAY/sram_lib/2007 resources/sram_lib',
    '/cad/libs/u18/u18_1.3 resources/u18',
    '/cad/libs/u18/FARADAY/fsa0m_a/2009Q2v2.0/GENERIC_CORE resources/fsa0m_a_sc',
    '/cad/libs/u18/FARADAY/fsa0m_a/2008Q3v1.2/T33_GENERIC_IO resources/fsa0m_a_t33_generic_io',
    '/cad/libs/u18/UMC_IMEC_BONDLIB/UMC_IMEC_BONDLIB_V1x3 resources/UMC_IMEC_BONDLIB',
    '/cad/libs/tsmc resources/tsmc',
    '/afs/kip/projects/vision/p_facets/s_minilink_dncif_2.0/units resources/tud_ipdev'
]

TMPS = ['cds/connectLibTMP']

subprocess.call(['mkdir', '-p', './resources'])
for path in PATHS:
    args = path.split(" ")
    print("Removing symbolic link "+args[1])
    subprocess.call(['rm','-f', args[1]])
    print("Linking "+args[1]+" to "+args[0])
    subprocess.call(['ln', '-s', args[0], args[1]])

for tmp in TMPS:
    print("Creating tmp directory ./tmp/"+tmp)
    subprocess.call(['mkdir', '-p', './tmp/'+tmp])

print("Done\n")

