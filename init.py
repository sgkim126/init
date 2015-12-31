#!/usr/bin/env python3
import functools
import os
import subprocess
import sys
import tarfile
import traceback
import urllib.request


def try_and_catch(function):
    try:
        function()
    except Exception as ex:
        print(ex)
        traceback.print_exc(file=sys.stdout)


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


def install(url, tarname, commands):
    home = os.getenv('HOME')
    prefix = os.path.join(home, '.root')
    opt = os.path.join(prefix, 'opt')
    seperator = os.sep
    tarpath = os.path.join(opt, tarname)
    name = tarname[:-7]  # remove .tar.gz
    path = os.path.join(opt, name)

    os.makedirs(opt, exist_ok=True)  # mkdir $HOME/.root/opt
    os.chdir(opt)
    if not os.path.exists(path):
        if not os.path.exists(tarpath):
            urllib.request.urlretrieve(url, tarname)
            tarfile.open(tarname).extractall()
        os.remove(tarpath)
    os.chdir(path)

    def call_commands():
        for command in commands(prefix, path):
            subprocess.call(command.split(' '))
    try_and_catch(call_commands)


def confirm(message):
    while True:
        i = input(message)
        if i == 'y':
            return True
        if i == 'n':
            return False


if __name__ == '__main__':
    if confirm('Do you want to install packages with sudo?(y/n) '):
        try_and_catch(functools.partial(
            apt_get_install, 'build-essential', 'clang'))

    if confirm('Do you want to initialize $HOME/.root directory?(y/n) '):
        try_and_catch(initialize_root)

    if confirm('Do you want to config git?(y/n) '):
        try_and_catch(git_config)

    if confirm('Do you want to install virtualenv?(y/n) '):
        def install_virtualenv_command(prefix, current_path):
            bin_path = os.path.join(prefix, 'bin')
            sym_path = os.path.join(bin_path, 'virtualenv')
            target = os.path.join(current_path, 'virtualenv.py')
            return ['rm -f %s' % sym_path,
                    'ln -s %s %s' % (target, sym_path)]
        try_and_catch(functools.partial(
            install,
            ('https://pypi.python.org/packages/source/v/virtualenv/'
             'virtualenv-13.1.2.tar.gz'),
            'virtualenv-13.1.2.tar.gz',
            install_virtualenv_command))

    if confirm('Do you want to install cmake?(y/n) '):
        def install_cmake(prefix, current_path):
            return ['./configure --prefix=%s' % prefix,
                    'make',
                    'make install']
        try_and_catch(functools.partial(
            install,
            'https://cmake.org/files/v3.4/cmake-3.4.1.tar.gz',
            'cmake-3.4.1.tar.gz',
            install_cmake))

    if confirm('Do you want to install libtool?(y/n) '):
        def install_libtool(prefix, current_path):
            return ['./configure --prefix=%s' % prefix,
                    'make',
                    'make install']
        try_and_catch(functools.partial(
            install,
            'http://ftpmirror.gnu.org/libtool/libtool-2.4.6.tar.gz',
            'libtool-2.4.6.tar.gz',
            install_libtool))

    if confirm('Do you want to install curl?(y/n) '):
        def install_commands(prefix, current_path):
            return ['./buildconf',
                    './configure --prefix=%s' % prefix,
                    'make',
                    'make install']
        try_and_catch(functools.partial(
            install,
            ('https://github.com/bagder/curl/releases/download/curl-7_46_0/'
             'curl-7.46.0.tar.gz'),
            'curl-7.46.0.tar.gz',
            install_commands))

    if confirm('Do you want to install git?(y/n) '):
        def install_commands(prefix, current_path):
            return ['make prefix=%s CURLDIR=%s NO_R_TO_GCC_LINKER=1 install'
                    % (prefix, prefix)]
        try_and_catch(functools.partial(
            install,
            'https://github.com/git/git/archive/v2.6.4.tar.gz',
            'git-2.6.4.tar.gz',
            install_commands))
