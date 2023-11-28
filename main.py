import requests
import os
import configparser

config = configparser.ConfigParser()
config.read("config.ini")
SERVER_URL = config.get("config", "server_url")
API_KEY = config.get("config", "api_key")
PARENT = config.get("config", "parent_collection")

# API_KEY = config.access_token_ddvnl # dataverse API key
# SERVER_URL = config.SERVER_URL_DDVNL # dataverse server
BASE_URL = '{server_url}/api/v1/{endpoint}'

headers = {
    'X-Dataverse-key': API_KEY,
    'Content-Type': 'application/json'
}

def create_dataset(filename):
    if not os.path.exists(filename):
        print('Data file does not exist')
        return
    
    with open(filename, 'r') as f:
        data = f.read()

    url = BASE_URL.format(server_url = SERVER_URL, endpoint = f'dataverses/{PARENT}/datasets')

    response = requests.post(url=url, headers=headers, data=data)
    if response.status_code != 201:
        print('Something is wrong', response.content)
        return None, None

    id = response.json()['data']['id']
    doi = response.json()['data']['persistentId']
    print(f'Dataset created.\nDOI: {doi}, ID: {id}')

    return id, doi

def upload_files(doi):
    # files = {'file': ('files_1.json', open('./files/files_1.json', 'rb'))}
    # files = {
    #     'file1': ('files_1.json', open('./files/files_1.json', 'rb')),
    #     'file2': ('dataset_1.json', open('./datasets/dataset_1.json', 'rb'))
    # }
    if doi == None:
        print('No DOI')
        return

    files = {'file': ('data.zip', open('./data/Data.zip', 'rb'))}

    if not os.path.exists('./data/Data.zip'):
        print('File does not exist')
        return

    url = BASE_URL.format(server_url = SERVER_URL, endpoint=f'datasets/:persistentId/add?persistentId={doi}&key={API_KEY}')
    response = requests.post(url, files=files)

    if response.status_code != 200:
        print('Something is wrong', response.content)

    print(f'Files uploaded to dataset with doi: {doi}')

def main():
    id, doi = create_dataset('create-dataset.json')
    if doi != None:
        upload_files(doi)

if __name__ == '__main__':
    main()