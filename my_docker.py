import subprocess, os, sys
import requests, json, tarfile

# Defining all pull url's 
AUTH_SERVICE_URL = "https://auth.docker.io/token"
SERVICE = "registry.docker.io"

jail_dir = "./jail_dir"

if not os.path.exists(jail_dir):
    print("Jail DIR doesn't exists")
    sys.exit(1)

############################# ! Isolation [Namespaces]
import ctypes   # helps in loading the C library
libc = ctypes.CDLL(None)   # Load the C standard library
CLONE_NEWPID = 0x20000000      # # Define the C constants for namespaces (from /usr/include/linux/sched.h)
CLONE_NEWNS = 0x00020000

def setup_namespace():
    # Calling the C function unshare(CLONE_NEWPID) -- This disconnects the process from the parent's PID tree
    flags = CLONE_NEWPID | CLONE_NEWNS
    ret = libc.unshare(flags)
    if ret == -1:
        raise OSError("Failed to unshare PID namespace. Are you running as sudo?")
############################# !

# ***************** The Puller ***********************#
def get_token(image):
    """Authenticate with Docker Hub and get a Bearer Token."""
    print(f"Authenticating for {image}...")
    params = {"service": SERVICE, "scope": f"repository:library/{image}:pull"}
    resp = requests.get(AUTH_SERVICE_URL, params)
    token = resp.json().get('token')
    return token

def pull_image(image_name):
    """Orchestrates the manifest fetch and layer download."""
    token = get_token(image_name)
    header = {"Authorization": f"Bearer {token}"}
    print(f"Fetching manifest for {image_name}...")

    """ Get Manifest List """
    REGISTRY_URL = f"https://registry-1.docker.io/v2/library/{image_name}/manifests/latest"
    res = requests.get(REGISTRY_URL, headers=header)
    
    status_code = res.status_code
    if status_code != 200:
        print(f"Failed! Status: {res.status_code}")
        print(res.text)
        sys.exit(1)
        
    """ Find AMD64/Linux Digest """
    target_digest = None
    for item in res.json().get('manifests', []):
        platform = item.get('platform')
        arch = platform.get('architecture')
        oss = platform.get('os')
        if arch == "amd64" and oss == "linux":
            target_digest = item.get('digest')
            break
    
    if not target_digest:
        print("Error: Could not find amd64/linux version.")
        sys.exit(1)
        
    """ Get Actual Image Manifest """
    IMAGE_URL = f"https://registry-1.docker.io/v2/library/{image_name}/manifests/{target_digest}"
    img_data = requests.get(IMAGE_URL, headers=header)
    
    layers = img_data.json().get('layers') 
    mediaType = layers[0].get('mediaType')
    digest = layers[0].get('digest')
    
    """ Downloading Layer """
    print(f"Downloading layer: {digest[:12]}...")
    BLOB_URL = f"https://registry-1.docker.io/v2/library/{image_name}/blobs/{digest}"
    blob_res = requests.get(BLOB_URL, headers=header, stream=True)
    
    filename = "alpine-layer.tar.gz"
    with open(filename, "wb") as f:
        # instead of loading entire file in ram, load it in chunks
        for chunk in blob_res.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    
    """ Extracting the file """
    print(f"Extracting to {jail_dir}...")
    
    if not os.path.exists("./jail_dir"):
        os.makedirs("./jail_dir")
    
    with tarfile.open(filename, "r:gz") as tar:
        tar.extractall(path="./jail_dir")
    os.remove(filename)
    print(f"Success! Image pulled and extracted.")
    
# ***************** XXXXXXX **************************#

# ? **************** The Runner ***********************#

def run_container(command, args):
    """Runs the command in an isolated container."""
    print(f"🚀 Starting container: {command} {' '.join(args)}")

    setup_namespace()
    pid = os.fork()  # ? Create a child process of the parent
    
    if pid == 0:
        # * Child Process
        try:
            os.chroot(jail_dir) # change root of the container inside jail_dir -- it changes the root
            os.chdir('/') # Even after chainging root, you still standing outside jail. It redirects you on new root
        except Exception as e:
            print("Error occurred. Failed to chroot", e)
            sys.exit(1)
        
        # Mount the proc -- lazy way
        subprocess.run(["mount", "-t", "proc", "proc", "/proc"])
        print("/proc mounted successfully to jail dir")
        
        complete_args = [command] + args
        try:
            # we don't want container to be a child [if use subprocess].. We want container to be a process
            os.execvp(command, complete_args)
        except Exception as e:
            print(f"Command not found: {complete_args}")
            sys.exit(1)
    else:
        # * Its Parent Process
        print(f"Parent: Created container process with Host PID {pid}")
        status = os.waitpid(pid, 0)
        print(f"Parent: Container exited with status {status}")

# ? **************** XXXXXXX **************************#


######################## Main Function ########################

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Script Usage: [ sudo python3 my_docker.py [run|pull] args ]")
        sys.exit(1)
        
    action = sys.argv[1]
    
    if action == "pull":
        image = sys.argv[2] if len(sys.argv) > 2 else "alpine"
        pull_image(image)
        
    elif action == "run":
        if len(sys.argv) < 3:
            print(f"Script Usage: [ python3 ./script run <command> <argument> ]")
            sys.exit(1)
        command = sys.argv[2]
        args = sys.argv[3:]     # 3 and after 3 are all arguments

        run_container(command, args)
    else:
        print(f"{action} not justified. use [run | pull]")
######################## ############# ########################