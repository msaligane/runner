#!/usr/bin/python3
import sys, subprocess, json, click, paramiko, time, functools
from collections import namedtuple

print = functools.partial(print, flush=True)

USER = 'scalerunner'

def load_config():
    with open('../.vm_specs.json', 'r') as f:
        return json.load(f, object_hook=lambda d: namedtuple('vm_specs', d.keys())(*d.values()))

def elapsed(start):
    return round(time.time() - start, 2)

def get_ssh():
    ssh = paramiko.SSHClient()
    ssh.get_host_keys()
    ssh.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
    return ssh

@click.command()
@click.option('-n', '--instance-number', help='Instance number', required=True)
@click.option('-s', '--container-file', help='Container file', required=True)
def main(instance_number, container_file):
    c = load_config()

    machine_type = c.gcp.type
    overlay_size_gb = c.machine.disk

    project_id = c.gcp.project
    zone = c.gcp.zone
    instance_name = f'auto-spawned{instance_number}'

    print(f'Spawning a GCP machine in {c.gcp.zone}...')
    print(f'Instance name:\t {instance_name}')
    print(f'Instance type:\t {c.gcp.type}')
    print(f'Disk type:\t {c.gcp.disk_type}')

    key = (open('/home/runner/.ssh/id_rsa.pub')
          .read()
          .strip()
	  .translate(str.maketrans({'+': r'\+', ' ': r'\ '}))	
    )

    gcloud_start = time.time()

    try:
        output = subprocess.check_output(
                'gcloud beta compute --verbosity=error '
                f'--project={c.gcp.project} '
                f'instances create {instance_name} --zone={c.gcp.zone} '
                f'--machine-type={machine_type} --subnet={c.gcp.subnet} '
                '--no-address --network-tier=PREMIUM '
                '--metadata=serial-port-enable=true,'
                'ssh-keys=coordinator:'
                f'{key} '
                '--no-restart-on-failure --tags=runners '
                '--maintenance-policy=TERMINATE --preemptible '
                '--no-service-account '
                '--no-scopes '
                f'--image={c.gcp.image} --image-project={c.gcp.project} '
                f'--boot-disk-size={overlay_size_gb}GB '
                f'--boot-disk-type={c.gcp.disk_type} '
                f'--boot-disk-device-name={instance_name} '
                '--reservation-affinity=any',
                shell=True,
                stderr=subprocess.STDOUT,
        ).decode("utf-8")

        print('\n'+output.replace(c.gcp.project, '***'))

    except subprocess.CalledProcessError as err:
        print('\n'+err.output.decode().replace(c.gcp.project, '***'))
        exit()

    print(f'Machine spawned in {elapsed(gcloud_start)} seconds.')
    
    # this is the name recognized by DNS in Google
    target = f'{instance_name}.{c.gcp.zone}.c.{c.gcp.project}.internal'

    try_ssh = get_ssh()
    try_ssh_timeout = try_ssh_timeout_c = 40

    while try_ssh_timeout_c > 0:
        try:
            try_ssh.connect(
                    target,
                    username=USER,
                    password=USER,
                    timeout=1,
                    auth_timeout=1,
                    banner_timeout=1,
            )
            print('SSH is operational!')

            _, stdout, stderr = try_ssh.exec_command('sudo chown -R {0}:{0} /home/{0}'.format(USER))
            stdout_lines = stdout.readlines()
            stderr_lines = stderr.readlines()

            for l in stdout_lines:
                print(l.strip())

            for l in stderr_lines:
                print(l.strip())

            try_ssh.close()
            break
        except Exception as e:
            print('[{}/{}] Waiting for SSH...'.format(try_ssh_timeout_c, try_ssh_timeout))
            try_ssh_timeout_c -= 1

            if try_ssh_timeout_c == 0:
                print('Timeout while waiting for SSH!')
                sys.exit(1)

            time.sleep(1)

    # scp public key to authorized_keys of the minion machine
    try:
        result = subprocess.check_output(
                'sshpass -p scalerunner scp -q '
                '-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no '
                f'~/.ssh/id_rsa.pub scalerunner@{target}:~/.ssh/authorized_keys ',
                shell=True
        )
    except subprocess.CalledProcessError as err:
        print('Failed to copy public ssh key to authorized_keys of the runner:')
        print(err)

    ssh = get_ssh()
    ssh.connect(target, username='scalerunner')

    sif_location = '/mnt/container.sif'

    commands = (
        'uname -a',
        'sudo mkdir -p /mnt/1 /mnt/2/work /mnt/3',
        f'echo "Pulling {container_file}..."',
	    f'sudo singularity pull {sif_location} docker://{container_file}',
        f'sudo singularity instance start -C -e --dns 8.8.8.8 --overlay /mnt/1 --bind /mnt/2:/root {sif_location} i',
        'sudo iptables -A OUTPUT -d 169.254.169.254 -j DROP'
        #'SARGRAPH_OUTPUT_TYPE=svg sargraph chart start',
    )

    for cmd in commands:
        _, stdout, stderr = ssh.exec_command(cmd)

        stdout_lines = stdout.readlines()
        stderr_lines = stderr.readlines()

        for l in stdout_lines:
            print(l.strip())

        for l in stderr_lines:
            print(l.strip())

if __name__ == '__main__':
    main()
