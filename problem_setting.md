To set a problem on the judge, first ask me (jiminycricket#2701) to provide you with problem setting permissions (previous admins should already have the permissions). Open a direct message with the judge bot (Judge#5642) or a secure private channel with the judge and upload a zip file with the problem data contents, along with the comment `-export`.

The zip file contents should contain the following files:
1. A `params.yaml` file containing the following information:
```
name: problemName
difficulty: numberOfPoints
timelimit: [timeLimitPython, timeLimitJava, timeLimitC++]
batches: [casesInBatch1, casesInBatch2, ...]
points: [pointsForBatch1, pointsForBatch2, ...]
private: 1 for true 0 for false
contest: contestName  [should only be set if "private" is true]
```
(all problems have a memory limit of 256 MB)

2. A problem statement description contained in the file `description.md`
3. Testdata: Every test data file will start with `data`, followed by the batch number, followed by a `.`, followed by the case number, followed by either `.in` for an input file or `.out` for an output file. For example, `data3.2.out` is the output file for batch 3 case 2 of the testdata.

Please do not zip a folder containing these files; directly zip the file contents only.
After you upload the problem data, only you will be able to re-upload and modify the problem contents.