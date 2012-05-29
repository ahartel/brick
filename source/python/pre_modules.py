from preRunHook import preRunHook
import os
import re
import subprocess
import time
import ConfigParser

@preRunHook
def modules_prerun_hook(brick):
    module_string = ''
    try:
        for name,value in brick.config.items('modules'):
            module_string += name+'/'+value+' '
    except ConfigParser.NoSectionError:
        logger.debug("Section 'modules' missing in config file. Not loading any modules.")
        return True

    p = subprocess.Popen('bash /usr/local/Modules/current/init/bash && module purge && module load '+module_string+' && export -p', shell=True, stdout=subprocess.PIPE)
    time.sleep(1)
    for line in p.stdout:
        m = re.search('(\w+)=(".+")$', line)
        if (m):
            os.environ[m.group(1)] = m.group(2)

    return True
