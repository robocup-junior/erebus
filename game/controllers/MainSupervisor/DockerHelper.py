
from ConsoleLog import Console
import subprocess
import socket

EREBUS_IMAGE = "alfredroberts/erebus:latest"
EREBUS_CONTROLLER_TAG = "erebus_internal"

def _erebus_image_exists() -> bool:
    """Check if the host machine has an erebus docker image 

    Returns:
        bool: True if the {EREBUS_IMAGE} image is found
    """
    try:
        process: subprocess.CompletedProcess = subprocess.run(
            [f"docker inspect {EREBUS_IMAGE}"],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
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
        sock.connect(('foo.foo.foo.foo', 1))
        ip_addr: str = sock.getsockname()[0]
    except:
        raise Exception("Could not find local ip address")
    finally:
        sock.close()
    return ip_addr

def run_docker_container(project_dir: str) -> bool:
    """Run a controller via a docker container

    Args:
        project_dir (str): System path to directory containing a Dockerfile

    Returns:
        bool: True if docker container runs successfully
    """
    Console.log_info(f"Checking if erebus image exists (tag={EREBUS_IMAGE})")
    if not _erebus_image_exists():
        Console.log_err(f"Could not find docker image {EREBUS_IMAGE}. Run: docker pull {EREBUS_IMAGE} to download the latest version.")
        return False
    
    try:
        ip_address = _get_local_ip()
    except Exception as e:
        Console.log_err(f"{e}. Unable to run docker container")
        return False
    Console.log_info(f"Using local ip address: {ip_address}")
    
    # Build container
    try:
        command: str = f"docker build --tag {EREBUS_CONTROLLER_TAG} {project_dir}"
        Console.log_info(f"Building project image ($ {command})")
        build_process: subprocess.CompletedProcess = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
    except Exception as e:
        Console.log_err(f"Error building project image - {e}")
        return False
    
    if build_process.returncode != 0:
        Console.log_err(f"Unable to build project image - {build_process.stdout.decode().strip()}")
        return False
    
    # Run container
    try:
        command: str = f"docker run --env EREBUS_SERVER={ip_address} --rm '{EREBUS_CONTROLLER_TAG}'"
        Console.log_info(f"Running container ($ {command})")
        run_process: subprocess.Popen = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
    except Exception as e:
        Console.log_err(f"Error running project image - {e}")
        return False
    
    while run_process.poll() is None:
        if run_process.stdout:
            line = run_process.stdout.readline().rstrip()
            Console.log_controller(line.decode())
    
    return True