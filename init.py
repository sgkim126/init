#!/usr/bin/env python3
import os
import subprocess
import sys
import tarfile
import traceback
import urllib.request


def apt_get_install(packages):
    subprocess.call(['sudo', 'apt-get', 'update'])
    subprocess.call(['sudo', 'apt-get', 'upgrade', '-y'])
    apt_get_command_without_target = ['sudo', 'apt-get', 'install', '-y']
    for package in packages:
        subprocess.call(apt_get_command_without_target + package)


def initialize_root():
    home = os.getenv('HOME')
    prefix = os.path.join(home, '.root')

    dirs = []
    dirs.append(os.path.join(prefix, 'bin'))
    dirs.append(os.path.join(prefix, 'include'))
    dirs.append(os.path.join(prefix, 'lib'))
    dirs.append(os.path.join(prefix, 'opt'))
    dirs.append(os.path.join(prefix, 'tmp'))
    dirs.append(os.path.join(prefix, 'var'))
    share = os.path.join(prefix, 'share')
    dirs.append(share)
    dirs.append(os.path.join(share, 'doc'))
    dirs.append(os.path.join(share, 'info'))
    dirs.append(os.path.join(share, 'man'))

    for dir in dirs:
        os.makedirs(dir, exist_ok=True)


def git_config():
    def global_config(attribute, value):
        subprocess.call(['git', 'config', '--global'] + [attribute, value])
    global_config('color.ui', 'auto')
    global_config('color.ui', 'auto')
    global_config('core.editor', 'vim')
    global_config('core.excludefile', '~/.gitignore')
    global_config('diff.noprefix', 'true')

    name = input("Enter your name for git: ")
    if name != '':
        global_config('user.name', name)
    mail = input("Enter your mail address for git: ")
    if mail != '':
        global_config('user.email', mail)
    username = input("Enter your github username: ")
    if username != '':
        global_config('github.user', username)


def confirm(message):
    while True:
        i = input(message)
        if i == 'y':
            return True
        if i == 'n':
            return False


if __name__ == '__main__':
    try:
        if confirm('Do you want to install packages with sudo?(y/n) '):
            apt_get_install(['build-essential', 'clang'])
    except Exception as ex:
        print(ex)
        traceback.print_exc(file=sys.stdout)

    try:
        if confirm('Do you want to initialize $HOME/.root directory?(y/n) '):
            initialize_root()
    except Exception as ex:
        print(ex)
        traceback.print_exc(file=sys.stdout)

    try:
        if confirm('Do you want to config git?(y/n) '):
            git_config()
    except Exception as ex:
        print(ex)
        traceback.print_exc(file=sys.stdout)
