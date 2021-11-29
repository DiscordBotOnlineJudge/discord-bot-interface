def get_file(storage_client, blobname, save):
    blob = storage_client.blob(blobname)
    blob.download_to_filename(save)

def write_file(storage_client, problem, bat, case, ext, save):
    blob = storage_client.blob("TestData/" + problem + "/data" + str(bat) + "." + str(case) + "." + ext)
    blob.download_to_filename(save)
    
    