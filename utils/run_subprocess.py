def run_subprocess(running_procs,timeout=3600):
    proc_comms = []
    for proc_com in running_procs.communicate(timeout=timeout):
        print(proc_com)
        proc_comms.append(proc_com)
        if "Triggered retrieval from the Long Term Archive" in str(proc_com):
            assert(0)

    retcode = running_procs.poll()
        # print(retcode)

    if retcode != 0:
       print("Error:", retcode)

    return proc_comms
