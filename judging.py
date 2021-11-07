# This file contains methods that the judge uses to determine
# a verdict for a submission test case

import time
import os
import subprocess
import math
import asyncio
import resource

def limit_virtual_memory():
    MAX_VIRTUAL_MEMORY = 256 * 1024 * 1024 # MB
    resource.setrlimit(resource.RLIMIT_AS, (MAX_VIRTUAL_MEMORY, resource.RLIM_INFINITY))

def cleanChecker(fn, jn):
    f = open(fn, "r")
    src = f.read().replace("data.in", "Judge" + jn + "/data.in").replace("data.out", "Judge" + jn + "/data.out")
    f.flush()
    f.close()

    w = open(fn, "w")
    w.write(src)
    w.flush()
    w.close()

def cleanNullChars(output):
    res = ""
    for x in output:
        if ord(x) != 0:
            res += x
    return res

def checkEqual(problem, bat, case, judgeNum, storage_client):
    try:
        get_file(storage_client, "TestData/" + problem + "/checker.py", "Judge" + str(judgeNum) + "/checker.py")
        myOutput = open("Judge" + str(judgeNum) + "/verdict.out", "w") 

        cleanChecker("Judge" + str(judgeNum) + "/checker.py", str(judgeNum))

        check = subprocess.Popen("python3 Judge" + str(judgeNum) + "/checker.py Judge" + str(judgeNum) + "/data.in Judge" + str(judgeNum) + "/data.out", stdout=myOutput, shell=True)
        code = check.wait(3)

        if code != 0:
            return False

        myOutput.flush()
        myOutput.close()

        with open("Judge" + str(judgeNum) + "/verdict.out") as f:
            v = f.read().strip() == "AC"
            f.close()
            return v

    except:
        write_file(storage_client, problem, bat, case, "out", "Judge" + str(judgeNum) + "/expected.out")

        cor = open("Judge" + str(judgeNum) + "/expected.out", "r")
        giv = open("Judge" + str(judgeNum) + "/data.out", "r")

        expect = cor.read()
        mine = giv.read()

        giv.flush()
        giv.close()
        cor.flush()
        cor.close()

        return cleanNullChars(expect).strip() == cleanNullChars(mine).strip()

def get_file(storage_client, blobname, save):
    blob = storage_client.blob(blobname)
    blob.download_to_filename(save)

def write_file(storage_client, problem, bat, case, ext, save):
    blob = storage_client.blob("TestData/" + problem + "/data" + str(bat) + "." + str(case) + "." + ext)
    blob.download_to_filename(save)

def judge(problem, bat, case, compl, cmdrun, judgeNum, timelim, username, sc):
    if bat <= 1 and case <= 1 and len(compl) > 0:
        anyErrors = open("Judge" + str(judgeNum) + "/errors.txt", "w")
        stdout = open("Judge" + str(judgeNum) + "/stdout.txt", "w")
        comp = subprocess.Popen(compl, stdout=stdout, stderr=anyErrors, shell=True)

        try:
            comp.wait(timeout = 5)
            anyErrors.flush()
            anyErrors.close()
            stdout.flush()
            stdout.close()
        except subprocess.TimeoutExpired:
            return ("Compilation Error: Request timed out", 0)

        if not comp.poll() == 0:
            return ("Compilation Error", 0)

    write_file(sc, problem, bat, case, "in", "Judge" + str(judgeNum) + "/data.in")

    myInput = open("Judge" + str(judgeNum) + "/data.in", "r")
    myOutput = open("Judge" + str(judgeNum) + "/data.out", "w")
    anyErrors = open("errors.txt", "w")
    
    proc = subprocess.Popen(cmdrun, stdin=myInput, stdout=myOutput, stderr=anyErrors, shell=True)

    tle = False
    startTime = time.time()
    while proc.poll() is None:
        if time.time() - startTime > timelim:
            tle = True
            break

    ft = time.time() - startTime
    taken = "{x:.3f}".format(x = ft)

    poll = proc.poll()
    proc.terminate()
    myInput.close()
    myOutput.flush()
    anyErrors.flush()
    myOutput.close()
    anyErrors.close()

    ts = "{x:.3f}".format(x = timelim)

    if tle:
        return ("Time Limit Exceeded [>" + str(ts) + " seconds]", ft)
    elif not poll == 0:
        return ("Runtime/Memory Error (Exit code " + str(poll) + ") [" + taken + " seconds]", ft)
    
    try:
        if checkEqual(problem, bat, case, judgeNum, sc):
            return ("Accepted [" + taken + " seconds]", ft)
        else:
            return ("Wrong Answer [" + taken + " seconds]", ft)
    except Exception as e:
        print("Fatal error during grading:\n", str(e))
        return ("Internal System Error [" + taken + " seconds]", ft)
