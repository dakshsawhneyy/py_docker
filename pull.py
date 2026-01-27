import requests, json, os, tarfile

# Auth 
AUTH_SERVICE_URL = "https://auth.docker.io/token"
parameters = {
    "service": "registry.docker.io",
    "scope": "repository:library/alpine:pull"       # Read Only access to Alpine Repo
}

try:
    token_response = requests.get(AUTH_SERVICE_URL, parameters)
    token = token_response.json().get('token')
    # print(token)
except Exception as e:
    print(f"Error Occurred", e)
    
# Pulling Image
REGISTRY_URL = "https://registry-1.docker.io/v2/library/alpine/manifests/latest"
header = {
    "Authorization": f"Bearer {token}"
}

try:
    req_response = requests.get(REGISTRY_URL, headers=header)
    
    status_code = req_response.status_code
    if status_code != 200:
        print(f"Failed! Status: {req_response.status_code}")
        print(req_response.text)
        sys.exit(1)
    
    # print(json.dumps(req_response.json(), indent=4))
except Exception as e:
    print(f"Error Occurred: ", e)
    

# ? Need to fetch digest to provide for which system and os, we need the image
# Looping over req_response to find the entry where architecture is amd64 and os is linux
for item in req_response.json().get('manifests', []):
    platform = item.get('platform')
    arch = platform.get('architecture')
    oss = platform.get('os')
    
    if arch == "amd64" and oss == "linux":
        target_digest = item.get('digest')
        # print(f"Found amd64 digest: {target_digest}")
        break


# ? Fetching Actual Image
IMAGE_URL = f"https://registry-1.docker.io/v2/library/alpine/manifests/{target_digest}"
image_resp = requests.get(IMAGE_URL, headers=header)

layers = image_resp.json().get('layers') 
mediaType = layers[0].get('mediaType')
digest = layers[0].get('digest')

# Downloading the Blob
BLOB_URL = f"https://registry-1.docker.io/v2/library/alpine/blobs/{digest}"
blob_res = requests.get(BLOB_URL, headers=header, stream=True)
# print(blob_res.json())

filename = "alpine-layer.tar.gz"
with open(filename, "wb") as f:
    # instead of loading entire file in ram, load it in chunks
    for chunk in blob_res.iter_content(chunk_size=1024):
        if chunk:
            f.write(chunk)
            
print("Download complete. Extracting to jail_dir...")

if not os.path.exists("./jail_dir"):
    os.makedirs("./jail_dir")

# Extract tarfile inside jail_dir
with tarfile.open(filename, "r:gz") as tar:
    tar.extractall(path="./jail_dir")
    
os.remove(tar_name)    

print(f"Success! Image pulled and extracted.")