from tools.prepare.prepareHook import prepareHook
from prepareError import prepareError

@prepareHook('genLIB')
def prepare_genLIB(config,sectionName,options):
    "This module needs the option 'input'"

    return [],[],''

