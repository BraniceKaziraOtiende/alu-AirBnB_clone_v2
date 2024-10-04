#!/usr/bin/python3
"""
Fabric script based on the file 2-do_deploy_web_static.py that creates and
distributes an archive to the web servers

execute: fab -f 3-deploy_web_static.py deploy -i ~/.ssh/id_rsa -u ubuntu
"""

from fabric import task
from datetime import datetime
from os.path import exists, isdir
from fabric.connection import Connection

# List of server IPs
servers = ['3.80.78.52', '3.88.228.75']


@task
def do_pack(c):
    """Generates a tgz archive."""
    try:
        date = datetime.now().strftime("%Y%m%d%H%M%S")
        if isdir("versions") is False:
            c.local("mkdir versions")
        file_name = "versions/web_static_{}.tgz".format(date)
        c.local("tar -cvzf {} web_static".format(file_name))
        return file_name
    except Exception as e:
        print(f"Error during packing: {e}")
        return None


@task
def do_deploy(c, archive_path):
    """Distributes an archive to the web servers."""
    if exists(archive_path) is False:
        print("Archive path does not exist")
        return False

    try:
        file_n = archive_path.split("/")[-1]
        no_ext = file_n.split(".")[0]
        path = "/data/web_static/releases/"

        # Upload the archive
        c.put(archive_path, '/tmp/')
        # Create the release directory
        c.run('mkdir -p {}{}/'.format(path, no_ext))
        # Uncompress the archive
        c.run('tar -xzf /tmp/{} -C {}{}/'.format(file_n, path, no_ext))
        # Delete the uploaded archive
        c.run('rm /tmp/{}'.format(file_n))
        # Move files out of the web_static folder
        c.run('mv {0}{1}/web_static/* {0}{1}/'.format(path, no_ext))
        # Delete the now-empty web_static directory
        c.run('rm -rf {}{}/web_static'.format(path, no_ext))
        # Remove the current symbolic link
        c.run('rm -rf /data/web_static/current')
        # Create a new symbolic link
        c.run('ln -s {}{}/ /data/web_static/current'.format(path, no_ext))
        
        return True
    except Exception as e:
        print(f"Error during deployment: {e}")
        return False


@task
def deploy(c):
    """Creates and distributes an archive to the web servers."""
    archive_path = do_pack(c)
    if archive_path is None:
        return False

    # Iterate through the list of servers and deploy to each
    for server in servers:
        conn = Connection(host=server, user='ubuntu', connect_kwargs={"key_filename": "~/.ssh/id_rsa"})
        if not do_deploy(conn, archive_path):
            print(f"Deployment to {server} failed")
        else:
            print(f"Deployment to {server} succeeded")

