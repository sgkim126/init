#!/usr/bin/env python3
from functools import partial
import os
import subprocess
import sys
import tarfile
import traceback
import urllib.request


HOME = os.getenv('HOME')
PREFIX = os.path.join(HOME, '.root')
OPT_PATH = os.path.join(PREFIX, 'opt')
BIN_PATH = os.path.join(PREFIX, 'bin')


def try_and_catch(function):
    try:
        function()
    except Exception as ex:
        print(ex)
        traceback.print_exc(file=sys.stdout)


def apt_install(*packages):
    def apt_internal():
        if not confirm('Do you want to install packages with sudo?(y/n) '):
            return
        subprocess.call(['sudo', 'apt-get', 'update'])
        subprocess.call(['sudo', 'apt-get', 'upgrade', '-y'])
        apt_get_command_without_target = ['sudo', 'apt-get', 'install', '-y']
        for package in packages:
            subprocess.call(apt_get_command_without_target + package)
    try_and_catch(apt_internal)


def initialize_root():
    def initialize_root_internal():
        question = 'Do you want to initialize $HOME/.root directory? (y/n) '
        if not confirm(question):
            return

        dirs = [
            BIN_PATH,
            os.path.join(PREFIX, 'include'),
            os.path.join(PREFIX, 'lib'),
            OPT_PATH,
            os.path.join(PREFIX, 'tmp'),
            os.path.join(PREFIX, 'var'),
            os.path.join(PREFIX, 'share', 'doc'),
            os.path.join(PREFIX, 'share', 'info'),
            os.path.join(PREFIX, 'share', 'man')]

        for dir in dirs:
            os.makedirs(dir, exist_ok=True)

    try_and_catch(initialize_root_internal)


def config_git():
    def config_git_internal():
        if not confirm('Do you want to config git? (y/n) '):
            return

        def global_config(attribute, value):
            subprocess.call(['git', 'config', '--global'] + [attribute, value])

        global_config('color.ui', 'auto')
        global_config('color.ui', 'auto')
        global_config('core.editor', 'vim')
        global_config('core.excludesfile', '~/.gitignore')
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
    try_and_catch(config_git_internal)


def clone_git_repository(path, url):
    os.makedirs(path, exist_ok=True)
    os.chdir(path)
    if not os.path.exists('./.git'):
        subprocess.call(['git', 'init'])
        subprocess.call(['git', 'remote', 'add', 'origin', url])
    subprocess.call(['git', 'fetch', 'origin'])
    subprocess.call(['git', 'reset', '--hard', 'origin/master'])


def config_vim():
    def config_vim_internal():
        if not confirm('Do you want to config vim? (y/n) '):
            return

        url = 'https://github.com/sgkim126/dotvim.git'
        dotvim_path = os.path.join(HOME, '.vim')
        clone_git_repository(dotvim_path, url)

        dotvimrc_path = os.path.join(HOME, '.vimrc')
        vimrc_path = os.path.join(dotvim_path, 'vimrc')

        if os.path.exists(dotvimrc_path):
            os.remove(dotvimrc_path)
        os.symlink(vimrc_path, dotvimrc_path)

        subprocess.call(['vim', '+PlugInstall', '+qall'])

    try_and_catch(config_vim_internal)


def config_home():
    def config_home_internal():
        if not confirm('Do you want to config home? (y/n) '):
            return
        OPT_PATH = os.path.join(PREFIX, 'opt')
        dotfiles_path = os.path.join(OPT_PATH, 'dotfiles')
        url = 'https://github.com/sgkim126/dotfiles.git'
        clone_git_repository(dotfiles_path, url)
        dothome = os.path.join(dotfiles_path, 'home')
        files = os.listdir(dothome)
        for file in files:
            filename = '.%s' % file
            symfile = os.path.join(HOME, filename)
            if os.path.exists(symfile):
                os.remove(symfile)
            os.symlink(os.path.join(dothome, file), symfile)

    try_and_catch(config_home_internal)


def install(url, dirname, commands, env=None):
    if not confirm('Do you want to install %s? (y/n) ' % dirname):
        return
    seperator = os.sep
    tarname = url.split('/')[-1]
    tarpath = os.path.join(OPT_PATH, tarname)
    path = os.path.join(OPT_PATH, dirname)

    os.makedirs(OPT_PATH, exist_ok=True)  # mkdir $HOME/.root/opt
    os.chdir(OPT_PATH)
    if not os.path.exists(path):
        if not os.path.exists(tarpath):
            urllib.request.urlretrieve(url, tarname)
            tarfile.open(tarname).extractall()
        os.remove(tarpath)
    os.chdir(path)

    def call_commands():
        if env is None:
            custom_environ = os.environ
        else:
            custom_environ = os.environ.copy()
            custom_environ.update(env(path))
        for command in commands(path):
            process = subprocess.Popen(command.split(' '), env=custom_environ)
            while process.wait() is None:
                continue
    try_and_catch(call_commands)


def confirm(message):
    while True:
        i = input(message)
        if i == 'y':
            return True
        if i == 'n':
            return False


def install_virtualenv():
    def install_commands(current_path):
        sym_path = os.path.join(BIN_PATH, 'virtualenv')
        target = os.path.join(current_path, 'virtualenv.py')
        return ['rm -f %s' % sym_path,
                'ln -s %s %s' % (target, sym_path)]
    try_and_catch(partial(
        install,
        ('https://files.pythonhosted.org/packages/33/bc/'
         'fa0b5347139cd9564f0d44ebd2b147ac97c36b2403943dbee8a25fd74012/'
         'virtualenv-16.0.0.tar.gz'),
        'virtualenv-16.0.0',
        install_commands))


def install_cmake():
    def install_commands(current_path):
        cmake_path = os.path.join(PREFIX, 'cmake')
        return ['rm -rf %s' % cmake_path,
                'cp -rf %s %s' % (current_path, cmake_path),
                'rm -rf %s' % current_path, ]
    try_and_catch(partial(
        install,
        'https://cmake.org/files/v3.11/cmake-3.11.4-Linux-x86_64.tar.gz',
        'cmake-3.11.4-Linux-x86_64',
        install_commands))


def install_libtool():
    def install_commands(current_path):
        return ['./configure --prefix=%s' % PREFIX,
                'make',
                'make install',
                'rm -rf %s' % current_path, ]
    try_and_catch(partial(
        install,
        'http://ftpmirror.gnu.org/libtool/libtool-2.4.6.tar.gz',
        'libtool-2.4.6',
        install_commands))


def install_curl():
    def install_commands(current_path):
        return ['./buildconf',
                './configure --prefix=%s --with-ssl' % PREFIX,
                'make',
                'make install',
                'rm -rf %s' % current_path, ]
    try_and_catch(partial(
        install,
        'https://curl.haxx.se/download/curl-7.60.0.tar.gz',
        'curl-7.60.0',
        install_commands))


def install_git():
    def install_commands(current_path):
        new_work_dir = os.path.join(current_path, 'contrib', 'workdir',
                                    'git-new-workdir')
        bin_dir = os.path.join(PREFIX, 'bin', 'git-new-workdir')
        return ['make prefix=%s CURLDIR=%s NO_R_TO_GCC_LINKER=1 install'
                % (PREFIX, PREFIX),
                'rm -f %s' % bin_dir,
                'cp -f %s %s' % (new_work_dir, bin_dir),
                'rm -rf %s' % current_path, ]

    def get_env(current_path):
        return {'prefix': PREFIX, 'CURDIR': PREFIX}
    try_and_catch(partial(
        install,
        'https://github.com/git/git/archive/v2.18.0.tar.gz',
        'git-2.18.0',
        install_commands,
        get_env))


def install_node():
    def install_commands(current_path):
        node_home = os.path.join(PREFIX, 'node')
        return ['rm -rf %s' % node_home,
                'cp -rf %s %s' % (current_path, node_home),
                'rm -rf %s' % current_path, ]
    try_and_catch(partial(
        install,
        'https://nodejs.org/dist/v10.7.0/node-v10.7.0-linux-x64.tar.xz',
        'node-v10.7.0-linux-x64',
        install_commands))


def install_ant():
    def install_commands(current_path):
        ant_home = os.path.join(PREFIX, 'ant')
        return ['rm -rf %s' % ant_home,
                'cp -rf %s %s' % (current_path, ant_home),
                'rm -rf %s' % current_path, ]

    try_and_catch(partial(
        install,
        'http://apache.tt.co.kr//ant/binaries/apache-ant-1.9.6-bin.tar.gz',
        'apache-ant-1.9.6',
        install_commands))


def install_sbt():
    def install_commands(current_path):
        url = ('https://raw.githubusercontent.com/sgkim126/init/master/'
               'tools/generate_sbt.sh')
        script_name = url.split('/')[-1]
        script_path = os.path.join(current_path, script_name)
        sbt_path = os.path.join(BIN_PATH, 'sbt')
        jar_file = os.path.join(BIN_PATH, 'sbt-launch.jar')
        return [
            'mkdir -p %s' % BIN_PATH,
            'rm -f %s' % script_path,
            'curl %s -o %s' % (url, script_path),
            'rm -f %s' % sbt_path,
            'touch %s' % sbt_path,
            'chmod u+x %s' % sbt_path,
            'rm -f %s' % jar_file,
            'cp %s %s' % (os.path.join(current_path, 'bin', 'sbt-launch.jar'),
                          jar_file),
            'bash %s %s' % (script_path, PREFIX),
            'rm -f %s' % script_path,
            'rm -rf %s' % current_path,
        ]
    try_and_catch(partial(
        install,
        ('https://dl.bintray.com/sbt/native-packages/sbt/0.13.11/'
         'sbt-0.13.11.tgz'),
        'sbt',
        install_commands))


def install_pyenv():
    def install_commands(current_path):
        cmake_path = os.path.join(PREFIX, 'pyenv')
        return ['rm -rf %s' % cmake_path,
                'cp -rf %s %s' % (current_path, cmake_path),
                'rm -rf %s' % current_path, ]
    try_and_catch(partial(
        install,
        'https://github.com/pyenv/pyenv/archive/v1.2.5.tar.gz',
        'pyenv-1.2.5',
        install_commands))


def install_scala():
    def install_commands(current_path):
        scala_path = os.path.join(PREFIX, 'scala')
        return ['rm -rf %s' % scala_path,
                'cp -rf %s %s' % (current_path, scala_path),
                'rm -rf %s' % current_path]
    try_and_catch(partial(
        install,
        'http://downloads.lightbend.com/scala/2.11.8/scala-2.11.8.tgz',
        'scala-2.11.8',
        install_commands))


def install_neovim():
    def install_commands(current_path):
        install_prefix = '-DCMAKE_INSTALL_PREFIX=%s' % PREFIX
        flags = 'CMAKE_EXTRA_FLAGS+="%s"' % install_prefix
        build_type = 'CMAKE_BUILD_TYPE="Release"'
        return ['make %s %s' % (flags, build_type),
                'make install']
    try_and_catch(partial(
        install,
        'https://github.com/neovim/neovim/archive/v0.2.0.tar.gz',
        'neovim-0.2.0',
        install_commands))


def install_go():
    def install_commands(current_path):
        go_path = os.path.join(PREFIX, 'go')
        return ['rm -rf %s' % go_path,
                'cp -rf %s %s' % (current_path, go_path),
                'rm -rf %s' % current_path,
                'mkdir -p %s' % os.path.join(HOME, '.go')]
    try_and_catch(partial(
        install,
        'https://dl.google.com/go/go1.10.linux-amd64.tar.gz',
        'go',
        install_commands))


def install_hadoop():
    def install_commands(current_path):
        hadoop_home = os.path.join(PREFIX, 'hadoop')
        return ['rm -rf %s' % hadoop_home,
                'cp -rf %s %s' % (current_path, hadoop_home),
                'rm -rf %s' % current_path, ]
    try_and_catch(partial(
        install,
        ('http://apache.mirror.cdnetworks.com/hadoop/common/hadoop-2.7.2/'
         'hadoop-2.7.2.tar.gz'),
        'hadoop-2.7.2',
        install_commands))


if __name__ == '__main__':
    apt_install('build-essential', 'clang')

    initialize_root()

    config_home()
    config_git()
    config_vim()

    install_virtualenv()
    install_cmake()
    install_libtool()
    install_curl()
    install_git()
    install_node()
    install_ant()
    install_sbt()
    install_scala()
    install_pyenv()
    install_neovim()
    install_go()
    install_hadoop()
