from __future__ import annotations
from typing import TYPE_CHECKING
from typing import Optional

from ConsoleLog import Console
import subprocess
import socket
from threading import Thread

if TYPE_CHECKING:
    from MainSupervisor import Erebus

EREBUS_IMAGE = "alfredroberts/erebus:latest"
EREBUS_CONTROLLER_TAG = "erebus_internal"

def _erebus_image_exists() -> bool:
    """Check if the host machine has an erebus docker image 

    Returns:
        bool: True if the {EREBUS_IMAGE} image is found
    """
    try:
        process: subprocess.CompletedProcess = subprocess.run(
            ["docker", "inspect", EREBUS_IMAGE],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False
        )
    except Exception as e:
        Console.log_err(f"Error inspecting erebus image - {e}")
        return False
    
    output: str = process.stdout.decode()
    # docker inspect returns empty json output, so no image means
    # "[]" output
    return output[:2] != "[]"

def _get_local_ip() -> str:
    """Get local ip address of host machine

    Raises:
        Exception: Thrown if the ip address could not be found

    Returns:
        str: Local ipv4 address
    """
    # Set up UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(None)
    try:
        # Trick to find local ip address
        sock.connect(('foo.foo.foo.foo', 1))
        ip_addr: str = sock.getsockname()[0]
    except:
        raise Exception("Could not find local ip address")
    finally:
        sock.close()
    return ip_addr

def run_docker_container(
    erebus: Erebus, 
    project_dir: str,
) -> Optional[subprocess.Popen] | None:
    """Run a controller via a docker container

    Args:
        project_dir (str): System path to directory containing a Dockerfile

    Returns:
        Optional[subprocess.Popen]: Subprocess if docker container runs 
        successfully, None otherwise.
    """
    Console.log_info(f"Checking if erebus image exists (tag={EREBUS_IMAGE})")
    if not _erebus_image_exists():
        Console.log_err(f"Could not find docker image {EREBUS_IMAGE}. To fix this: \n"
                        f"\t1. Make sure the docker daemon is running. \n"
                        f"\t2. Run: `docker pull {EREBUS_IMAGE}` to download the latest version.")
        return None
    
    try:
        ip_address = _get_local_ip()
    except Exception as e:
        Console.log_err(f"{e}. Unable to run docker container")
        return None
    Console.log_info(f"Using local ip address: {ip_address}")
    
    # Build container
    try:
        command: list[str] = ["docker", "build", 
                              "--tag" ,EREBUS_CONTROLLER_TAG, project_dir]
        Console.log_info(f"Building project image ($ {' '.join(command)})")
        with subprocess.Popen(
            command,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
            bufsize=1, universal_newlines=True, shell=False, encoding="utf-8"
        ) as build_process:
            # Print output from build process
            if build_process.stdout:
                for line in build_process.stdout:
                    Console.log_info(line, sep=None, end='')
                    erebus.step(erebus.TIME_STEP)
                    
    except Exception as e:
        Console.log_err(f"Error building project image - {e}")
        return None
    
    if build_process.returncode != 0:
        Console.log_err(f"Unable to build project image")
        return None
    
    # Run container
    try:
        command: list[str] = ["docker", "run", 
                              "--env", f"EREBUS_SERVER={ip_address}", 
                              "--rm",
                              EREBUS_CONTROLLER_TAG]
        Console.log_info(f"Running container ($ {' '.join(command)})")
        run_process: subprocess.Popen = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=False,
        )
        # Thread to print non-blocking stdout from docker container
        thread: Thread = Thread(target=print_stdout, args=[run_process.stdout])
        thread.daemon = True # thread dies with the program
        thread.start()
    except Exception as e:
        Console.log_err(f"Error running project image - {e}")
        return None
    
    return run_process

def print_stdout(out) -> None:
    """Print a sub process's stdout to the erebus console
    
    Used for printing docker container outputs to the console

    Args:
        out (IO[bytes]): Popen subprocess stdout bytes buffer
    """
    for line in iter(out.readline, b''):
        print(line.decode())
    out.close()