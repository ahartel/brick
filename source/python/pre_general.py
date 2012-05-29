from preRunHook import preRunHook
import os

@preRunHook
def general_prerun_hook(brick):
    rundir = brick.get_full_rundir()
    # generate rundir
    if not os.path.isdir(rundir):
        os.mkdir(rundir)
    # generate logfile dir
    if not os.path.isdir(rundir+'/logfiles'):
        os.mkdir(rundir+'/logfiles')

    return True
