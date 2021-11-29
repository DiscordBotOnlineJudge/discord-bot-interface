import zipfile
import os
import yaml

def delete_blob(storage_client, blobname):
    blob = storage_client.blob(blobname)
    blob.delete()
    
def upload_blob(storage_client, file, blobname):
    blob = storage_client.blob(blobname)
    blob.upload_from_file(file)

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
    contest = ""
    try:
        contest = params['contest']
    except:
        pass
    settings.insert_one({"type":"problem", "name":params['name'], "points":params['difficulty'], "status":"s", "published":params['private'] == 0, "contest":contest})
    
    try:
        batches = params['batches']
        for x in range(1, len(batches) + 1):
            for y in range(1, batches[x - 1] + 1):
                upload_blob(storage_client, "problemdata/data" + str(x) + "." + str(y) + ".in", "TestData/" + params['name'])
                upload_blob(storage_client, "problemdata/data" + str(x) + "." + str(y) + ".out", "TestData/" + params['name'])
    except Exception as e:
        print(str(e))
        return "Error with uploading testdata"
    
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
        upload_blob(storage_client, "problemdata/cases.txt", "TestData/" + params['name'])
    except Exception as e:
        print(str(e))
        return "Error with uploading cases"
    
    if not existingProblem is None:
        if author != existingProblem['author']:
            return "Problem name already exists under another author"
        msg += "Problem with name " + params["name"] + " already exists. Editing problem.\n"
        settings.delete_one({"_id":existingProblem['_id']})
    
    msg += "Successfully uploaded problem data"
    return msg