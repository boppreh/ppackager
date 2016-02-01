"""
$ ppackage

Files:
[x] README (found README.md)
[x] LICENSE (found MIT)
[ ] INSTALL
[ ] CONTRIBUTING
[ ] CHANGES

Publishers:
[!] PyPI (taken)
[ ] Read The Docs (available)

Git:
[x] Is a repo
[x] Using Github (https://github.com/boppreh/ppackage)
[x] Is clean
"""
import re
import os
from pathlib import Path
from subprocess import check_output, CalledProcessError, STDOUT

here = Path('.')
OBLIGATORY = object()

help_messages = {
    'git_init': """This folder is not a Git repository. If you say yes, a new empty local repository will be created here. If you choose no, we continue from here ignoring everything related to Git.""",
    'create_gitignore': """ """,
    'set_github': """ """,
    'git_ssh': """ """,
    'git_sync': """ """,
    'commit_dirty': """ """,
}

class Supervisor(object):
    def __init__(self, options=None):
        self.options = options if options is not None else {}

    def ask(self, tag, question, default=OBLIGATORY):
        if tag in self.options:
            return self.options[tag]

        while True:
            response = input(question + ' ')
            if response == '?':
                print('\n\n' + help_messages[tag] + '\n\n')
            elif response:
                if response != default:
                    self.options[tag] = response
                return response
            elif default is not OBLIGATORY:
                return default

    def yes_or_no(self, tag, question, default):
        if tag in self.options:
            return self.options[tag]

        if default == True:
            response = input(question + ' [Y/n] ').lower()
        else:
            response = input(question + ' [y/N] ').lower()

        if response == '?':
            print('\n\n' + help_messages[tag] + '\n\n')
            return self.yes_or_no(tag, question, default)
        elif response == '':
            return default
        elif response.startswith('y'):
            if default is False:
                self.options[tag] = True
            return True
        elif response.startswith('n'):
            if default is True:
                self.options[tag] = False
            return False
        else:
            return self.yes_or_no(tag, question, default)

    def run(self, command, verbose=False):
        if verbose:
            print('  RUNNING {}'.format(command))
        return check_output(command, stderr=STDOUT).decode('utf-8')
    
    def ensure_git(self):
        try:
            self.run('git status')
        except CalledProcessError:
            if self.yes_or_no('git_init', 'Not a git repo. Initialize one?', True):
                self.run('git init')
                self.run('git commit --allow-empty -m "Create repo"')
            else:
                return

        gitignore = here / '.gitignore'
        if not gitignore.exists():
            if self.yes_or_no('create_gitignore', 'Missing git ignore. Create one?', True):
                with gitignore.open('w') as f:
                    f.write('*.pyc\n__pycache/')

        try:
            self.run('git fetch')
        except CalledProcessError:
            remote = ask('set_github', 'No remote set. Remote url (or none to skip):', None)
            if remote is not None:
                self.run(['git', 'remote', 'add', 'origin', remote])
                self.run('git push --set-upstream origin master')

        status = self.run('git status --porcelain')
        if re.search(r'^\?\? ', status) or re.search(r'^\s*M ', status):
            print('Repository has uncommitted files:')
            print(status)
            if self.yes_or_no('commit_dirty', 'Do you want to commit them now?', True):
                for status, name in re.findall('(..)\s(.+)', status):
                    if status == '??':
                        self.run(['git', 'add', name])
                os.system('git commit -a')

        origin_match = re.search(r'Fetch URL: (.+)', self.run('git remote show -n origin'))
        if origin_match:
            origin = origin_match.group(1)
            if origin.startswith('https://github.com'):
                if self.yes_or_no('git_ssh', 'Using HTTPS origin ({}). Switch to ssh?'.format(origin), True):
                    extract_pattern = 'https://github.com/(.+?)/(.+?)(?:.git)?$'
                    domain, user, repo = re.match(extract_pattern, origin).groups()
                    new_origin = 'git@github.com:{}/{}'.format(domain, user, repo)
                    self.run(['git', 'remote', 'set-url', 'origin', new_origin])

            sync_status = re.search(r'^## .+? \[(ahead|behind) (\d+)\]', self.run('git status --porcelain --branch'))
            if sync_status:
                direction, number = sync_status.groups(1)
                if self.yes_or_no('git_sync', '{} of remote by {} commits ({}). Perform sync now?'.format(direction.title(), number, origin), True):
                    self.run('git merge')
                    self.run('git push')
            
if __name__ == '__main__':
    s = Supervisor()
    try:
        s.ensure_git()
    finally:
        print(s.options)