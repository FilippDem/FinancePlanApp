#!/usr/bin/env python3
"""Run a command on the NAS via SSH. Usage: python nas_ssh.py 'command here'"""
import sys, paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.68.102', port=9222, username='Gonzik',
               password=open('C:/Users/filip/.nas_password').read().strip())
cmd = sys.argv[1]
full_cmd = 'export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/Volume1/@apps/DockerEngine/dockerd/bin && ' + cmd
stdin, stdout, stderr = client.exec_command(full_cmd)
out = stdout.read().decode()
err = stderr.read().decode()
if out: sys.stdout.buffer.write(out.encode('utf-8'))
if err: sys.stderr.buffer.write(err.encode('utf-8'))
sys.exit(stdout.channel.recv_exit_status())
