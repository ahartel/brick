cd <brick_checkout>
export ICPRO_DIR=`pwd`
python init-resources.py

In components muss ein checkout von ncf-hicann-fc liegen.
Dann:

./waf configure --configfile=config/fg_miniasic.xml
./waf build

Problem: genLIB wird immer wieder ausgef√hrt

