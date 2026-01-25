import sys
import subprocess
import os

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
    print(f"Container starting: {command} with args: {args} ")
    
    complete_args = [command] + args
    
    # it will replace python script with our command no children needed to run anything. parent runs and stops
    print(f"Debug: Python PID is {os.getpid()}. Replacing Process Now.....")
    
    # change root of the container inside jail_dir -- it changes the root
    os.chroot(jail_dir)
    # Even after chainging root, you still standing outside jail. It redirects you on new root
    os.chdir('/')
    
    # we don't want container to be a child [if use subprocess].. We want container to be a process
    os.execvp(command, complete_args)
    print("This will never print")