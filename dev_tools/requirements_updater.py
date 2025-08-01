import os

from deploy.AidLux.requirements_generator import aidlux_requirements_generate
from deploy.docker.requirements_generator import docker_requirements_generate
from deploy.headless.requirements_generator import headless_requirements_generate

# Ensure running in Alas root folder
os.chdir(os.path.join(os.path.dirname(__file__), '../'))


def _requirements_modify(text: str) -> str:
    """
    Modify dependency names
    zope-event -> zope.event
    zope-interface -> zope.interface

    zope-event and zope-interface will cause errors in low version of pip.

    ERROR: Could not install packages due to an EnvironmentError:
    [WinError 5] Access is denied: '....\\zope\\interface\\_zope_interface_coptimizations.cp37-win_amd64.pyd'
    Consider using the `--user` option or check the permissions.
    """
    text = text.replace('zope-event', 'zope.event')
    text = text.replace('zope-interface', 'zope.interface')
    return text


def requirements_modify(file='requirements.txt'):
    """
    DEPRECATED: This function is no longer used as ALAS now uses Poetry for dependency management.
    Legacy requirements.txt files are still generated for Docker and AidLux compatibility.
    """
    print(f'[DEPRECATED] requirements_modify: {file} - Use Poetry for main dependency management')
    if not os.path.exists(file):
        print(f'File {file} does not exist - skipping (Poetry is now used for main dependencies)')
        return
        
    with open(file, 'r') as f:
        text = f.read()

    text = _requirements_modify(text)

    with open(file, 'w') as f:
        f.write(text)


if __name__ == '__main__':
    print("ALAS now uses Poetry for dependency management.")
    print("Generating legacy requirements files for Docker and AidLux compatibility...")
    
    # Skip main requirements.txt as we use Poetry now
    # requirements_modify()
    
    # Generate specialized requirements for deployment environments
    aidlux_requirements_generate()
    docker_requirements_generate()
    headless_requirements_generate()