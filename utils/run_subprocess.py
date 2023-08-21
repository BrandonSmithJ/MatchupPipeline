def run_subprocess(running_procs,timeout=3600):
    for proc_com in running_procs.communicate(timeout=timeout):
        print(proc_com)

    retcode = running_procs.poll()
        # print(retcode)

    if retcode != 0:
       print("Error:", retcode)
