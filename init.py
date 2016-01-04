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
        ('https://pypi.python.org/packages/source/v/virtualenv/'
         'virtualenv-13.1.2.tar.gz'),
        'virtualenv-13.1.2',
        install_commands))


def install_cmake():
    def install_commands(current_path):
        return ['./configure --prefix=%s' % PREFIX,
                'make -- -DCMAKE_USE_OPENSSL=ON',
                'make install']
    try_and_catch(partial(
        install,
        'https://cmake.org/files/v3.4/cmake-3.4.1.tar.gz',
        'cmake-3.4.1',
        install_commands))


def install_libtool():
    def install_commands(current_path):
        return ['./configure --prefix=%s' % PREFIX,
                'make',
                'make install']
    try_and_catch(partial(
        install,
        'http://ftpmirror.gnu.org/libtool/libtool-2.4.6.tar.gz',
        'libtool-2.4.6',
        install_commands))


def install_curl():
    def install_commands(current_path):
        return ['./buildconf',
                './configure --prefix=%s' % PREFIX,
                'make',
                'make install']
    try_and_catch(partial(
        install,
        ('https://github.com/bagder/curl/releases/download/curl-7_46_0/'
         'curl-7.46.0.tar.gz'),
        'curl-7.46.0',
        install_commands))


def install_git():
    def install_commands(current_path):
        new_work_dir = os.path.join(current_path, 'contrib', 'workdir',
                                    'git-new-workdir')
        bin_dir = os.path.join(PREFIX, 'bin', 'git-new-workdir')
        return ['make prefix=%s CURLDIR=%s NO_R_TO_GCC_LINKER=1 install'
                % (PREFIX, PREFIX),
                'rm -f %s' % bin_dir,
                'cp -f %s %s' % (new_work_dir, bin_dir)]

    def get_env(current_path):
        return {'prefix': PREFIX, 'CURDIR': PREFIX}
    try_and_catch(partial(
        install,
        'https://github.com/git/git/archive/v2.6.4.tar.gz',
        'git-2.6.4',
        install_commands,
        get_env))


def install_node():
    def install_commands(current_path):
        return ['./configure --prefix=%s' % PREFIX,
                'make',
                'make install']
    try_and_catch(partial(
        install,
        'https://nodejs.org/dist/v5.3.0/node-v5.3.0.tar.gz',
        'node-5.3.0',
        install_commands))


def install_ant():
    def install_commands(current_path):
        return ['./build.sh install-lite']

    def get_env(current_path):
        return {'ANT_HOME': PREFIX}
    try_and_catch(partial(
        install,
        'http://apache.tt.co.kr//ant/source/apache-ant-1.9.6-src.tar.gz',
        'apache-ant-1.9.6',
        install_commands,
        get_env))


def install_sbt():
    def install_commands(current_path):
        url = ('https://raw.githubusercontent.com/sgkim126/init/master/'
               'tools/generate_sbt.sh')
        script_name = url.split('/')[-1]
        script_path = os.path.join(current_path, script_name)
        sbt_path = os.path.join(BIN_PATH, 'sbt')
        return [
            'mkdir %s' % BIN_PATH,
            'rm -f %s' % script_path,
            'curl %s -o %s' % (url, script_path),
            'rm -f %s' % sbt_path,
            'touch %s' % sbt_path,
            'chmod u+x %s' % sbt_path,
            'bash %s %s' % (script_path, PREFIX),
            'rm -f %s' % script_path,
        ]
    try_and_catch(partial(
        install,
        ('https://dl.bintray.com/sbt/native-packages/sbt/0.13.9/'
         'sbt-0.13.9.tgz'),
        'sbt',
        install_commands))


def install_python():
    def install_commands(current_path):
        return ['./configure --prefix=%s' % PREFIX,
                'make',
                'make install', ]
    try_and_catch(partial(
        install,
        'https://www.python.org/ftp/python/3.5.1/Python-3.5.1.tgz',
        'Python-3.5.1',
        install_commands))


def install_scala():
    def install_commands(current_path):
        source_path = os.path.join(current_path, 'bin')
        binaries = [
            'scalac',
            'fsc',
            'scala',
            'scalap',
            'scaladoc',
        ]
        source = parital(os.path.join, source_path)
        destination = parital(os.path.join, BIN_PATH)
        return ['ln -s %s %s' % (source(binary), destination(binary))
                for binary in binaries]
    try_and_catch(partial(
        install,
        'http://downloads.typesafe.com/scala/2.11.7/scala-2.11.7.tgz',
        'scala-2.11.7',
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
        'https://github.com/neovim/neovim/archive/v0.1.1.tar.gz',
        'neovim-0.1.1',
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
    install_python()
    install_neovim()
