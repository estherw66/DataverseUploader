import argparse, configparser, glob, os, requests, shutil

config = configparser.ConfigParser()
config.read("config.ini")
SERVER_URL = config.get("config", "server_url")
API_KEY = config.get("config", "api_key")
PARENT = config.get("config", "parent_collection")

BASE_URL = '{server_url}/api/v1/{endpoint}'
VALID_IMAGE_EXTS = ["jpg", "jpeg", "png", "bmp"]

def assert_dataset(path, dataset_type):
    datapath = os.path.join(path, "data")
    assert os.path.exists(datapath), "Dataset assertion failed: Input path must contain a folder named 'data'"
    datapaths = []
    trainpath = os.path.join(datapath, "train")
    if os.path.exists(trainpath): datapaths.append(trainpath)
    evalpath = os.path.join(datapath, "eval")
    if os.path.exists(evalpath): datapaths.append(evalpath)
    testpath = os.path.join(datapath, "test")
    if os.path.exists(testpath): datapaths.append(testpath)
    if len(datapaths) == 0: datapaths.append(datapath)
    for p in datapaths:
        if dataset_type == "tabular": assert_tabular_dataset(p)
        elif dataset_type == "classification": assert_classification_dataset(p)
        elif dataset_type == "object detection": assert_object_detection_dataset(p)

def assert_tabular_dataset(path):
    files = glob.glob(os.path.join(path, "*.csv"))
    assert len(files) > 0, "Tabular dataset assertion failed: " + path + " must contain at least 1 csv file."

def assert_classification_dataset(path):
    items = os.listdir(path)
    subfolders = [item for item in items if os.path.isdir(os.path.join(path, item)) and os.listdir(os.path.join(path, item))]
    assert len(subfolders) == len(items), "Classification dataset assertion failed: " + path + " must contain only non-empty folders."

def assert_object_detection_dataset(path):
    pvoc_files = glob.glob(os.path.join(path, "*.xml"))
    image_files = []
    for imgext in VALID_IMAGE_EXTS: image_files += glob.glob(os.path.join(path, "*." + imgext))
    assert len(pvoc_files) == len(image_files), "Object Detection dataset assertion failed: The number of images files does not match the number of pvoc xml files."
    unmatched_pvoc_files = []
    for pvoc_file in pvoc_files:
        pvoc_prefix = pvoc_file[:-4]
        found = False
        for img_file in image_files:
            if img_file.startswith(pvoc_prefix):
                found = True
                break
        if not found: unmatched_pvoc_files.append(pvoc_file)
    assert len(unmatched_pvoc_files) == 0, "Object Detection dataset assertion failed: The following pvoc xml files have no matching image: " + ",".join(unmatched_pvoc_files)

def create_dataset(name, description, author, affiliation, email):
    assert name != "", "name cannot be empty"
    assert description != "", "description cannot be empty"
    assert author != "", "author cannot be empty"
    assert affiliation != "", "affiliation cannot be empty"
    assert '@' in email and '.' in email, "email must be a valid email address"
    template = "./create-dataset.json"
    if not os.path.exists(template): raise Exception("missing template file:", template)
    with open(template, 'r') as f:
        data = f.read()
    data = data.replace("%NAME%", name)
    data = data.replace("%DESCRIPTION%", description)
    data = data.replace("%AUTHOR%", author)
    data = data.replace("%AFFILIATION%", affiliation)
    data = data.replace("%EMAIL%", email)
    url = BASE_URL.format(server_url=SERVER_URL, endpoint=f'dataverses/{PARENT}/datasets')
    response = requests.post(url=url, headers={"X-Dataverse-key": API_KEY, "Content-Type": "application/json"}, data=data)
    if response.status_code != 201: raise Exception("could not create dataset:", response.content)
    return response.json()["data"]["persistentId"]

def upload_files(doi, zipfile_path):
    assert doi != "", "doi cannot be empty"
    assert zipfile_path != "", "zipfile_path cannot be empty"
    assert zipfile_path.endswith(".zip"), "zipfile_path must have .zip extension"
    if not os.path.exists(zipfile_path): raise Exception("missing zipfile at path:", zipfile_path)
    files = {"file": ("data.zip", open(zipfile_path, 'rb'))}
    url = BASE_URL.format(server_url=SERVER_URL, endpoint=f'datasets/:persistentId/add?persistentId={doi}&key={API_KEY}')
    response = requests.post(url, files=files)
    if response.status_code != 200: raise Exception("could not upload zipfile to dataset:", response.content)

def main():
    parser = argparse.ArgumentParser(prog="DataverseUploader", description="Creates and uploads files to datasets on dataverse.")
    parser.add_argument("-i", required=True, help="Input path of the dataset files.")
    parser.add_argument("-n", required=True, help="Name of the dataset.")
    parser.add_argument("-t", required=True, choices=["tabular", "classification", "object detection"], help="Type of the dataset.")
    parser.add_argument("-d", required=True, help="Description of the dataset.")
    parser.add_argument("-a", required=True, help="Author name.")
    parser.add_argument("-f", required=True, help="Author affiliation.")
    parser.add_argument("-e", required=True, help="Author email address.")
    flags = vars(parser.parse_args())
    assert_dataset(flags["i"], flags["t"])
    shutil.make_archive("data", 'zip', flags["i"])
    doi = create_dataset(flags["n"], flags["d"], flags["a"], flags["f"], flags["e"])
    upload_files(doi, "data.zip")
    os.remove("data.zip")

if __name__ == '__main__':
    main()