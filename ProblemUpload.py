import zipfile
import os
import yaml
from google.cloud import storage

def delete_blob(storage_client, blobname):
    blob = storage_client.blob(blobname)
    blob.delete()
    
def upload_blob(storage_client, sourceName, blobname):
    bucket = storage_client.bucket('discord-bot-oj-file-storage')
    blob = bucket.blob(blobname)
    blob.upload_from_filename(sourceName)

def uploadProblem(settings, storage_client, url, author):
    msg = ""
    try:
        os.mkdir("problemdata")
    except:
        pass
    os.system("wget " + url + " -Q10k --timeout=3 -O data.zip")
    with zipfile.ZipFile("data.zip", 'r') as zip_ref:
        zip_ref.extractall("problemdata")
    
    params = yaml.safe_load(open("problemdata/params.yaml", "r"))
    existingProblem = settings.find_one({"type":"problem", "name":params['name']})

    if not existingProblem is None:
        if (not "author" in existingProblem) or author != existingProblem['author']:
            return "Error: problem name `" + params["name"] + "` already exists under another author"
        msg += "Problem with name `" + params["name"] + "` already exists. Editing problem and overwriting files.\n"
        settings.delete_one({"_id":existingProblem['_id']})

    contest = ""
    try:
        contest = params['contest']
    except:
        pass
    
    authors = params['authors']
    if not author in authors:
        authors.append(author)

    settings.insert_one({"type":"problem", "name":params['name'], "author":authors, "points":params['difficulty'], "status":"s", "published":params['private'] == 0, "contest":contest})

    batches = params['batches']
    for x in range(1, len(batches) + 1):
        for y in range(1, batches[x - 1] + 1):
            data_file_name = "data" + str(x) + "." + str(y)
            upload_blob(storage_client, "problemdata/" + data_file_name + ".in", "TestData/" + params['name'] + "/" + data_file_name + ".in")

            try:
                upload_blob(storage_client, "problemdata/" + data_file_name + ".out", "TestData/" + params['name'] + "/" + data_file_name + ".out")
            except:
                pass
    
    try:
        cases = open("problemdata/cases.txt", "w")
        for x in batches:
            cases.write(str(x) + " ")
        cases.write("\n")
        for x in params['points']:
            cases.write(str(x) + " ")
        cases.write("\n")
        for x in params['timelimit']:
            cases.write(str(x) + " ")
        cases.write("\n")
        cases.flush()
        cases.close()
        upload_blob(storage_client, "problemdata/cases.txt", "TestData/" + params['name'] + "/cases.txt")
    except Exception as e:
        print(str(e))
        return "Error with uploading cases"

    upload_blob(storage_client, "problemdata/description.md", "ProblemStatements/" + params['name'] + ".txt")
    
    try:
        upload_blob(storage_client, "problemdata/checker.py", "TestData/" + params['name'] + "/checker.py")
    except:
        pass
    
    msg += "Successfully uploaded problem data as problem `" + params['name'] + "`"
    return msg