import sys
import subprocess
import os

############################# ! Isolation [Namespaces]
# helps in loading the C library
import ctypes

# Load the C standard library
libc = ctypes.CDLL(None)

# Define the C constants for namespaces (from /usr/include/linux/sched.h)
CLONE_NEWPID = 0x20000000

def unshare_pid():
    # Calling the C function unshare(CLONE_NEWPID) -- This disconnects the process from the parent's PID tree
    ret = libc.unshare(CLONE_NEWPID)
    if ret == -1:
        raise OSError("Failed to unshare PID namespace. Are you running as sudo?")
############################# !

jail_dir = "./jail_dir"

if not os.path.exists(jail_dir):
    print("Jail DIR doesn't exists")
    sys.exit(1)

if len(sys.argv) < 3:
    print(f"Script Usage: [ python3 ./script run <command> <argument> ]")
    sys.exit(1)
    
command = sys.argv[2]
args = sys.argv[3:]     # 3 and after 3 are all arguments

if sys.argv[1] == "run":
    print(f"Parent: Setting up isolation...")
    
    # ? Create the new Namespace "Universe" - Any process created AFTER this call lives in the new namespace.
    unshare_pid()
    
    # ? Create a child process of the parent
    pid = os.fork()
    
    if pid == 0:
        # * Child Process
        try:
            os.chroot(jail_dir) # change root of the container inside jail_dir -- it changes the root
            os.chdir('/') # Even after chainging root, you still standing outside jail. It redirects you on new root
        except Exception as e:
            print("Error occurred. Failed to chroot", e)
            sys.exit(1)
        
        complete_args = [command] + args
        # we don't want container to be a child [if use subprocess].. We want container to be a process
        os.execvp(command, complete_args)
        print("This will never print")
    else:
        # * Its Parent Process
        print(f"Parent: Created container process with Host PID {pid}")
        status = os.waitpid(pid, 0)
        print(f"Parent: Container exited with status {status}")