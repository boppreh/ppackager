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
from pathlib import Path
from subprocess import check_output, CalledProcessError, STDOUT

here = Path('.')

OBLIGATORY = object()
class Supervisor(object):
    def ask(self, tag, question, default=OBLIGATORY):
        while True:
            response = input(question + ' ')
            if response:
                return response
            elif default is not OBLIGATORY:
                return default

    def yes_or_no(self, tag, question, default):
        if default == True:
            return not input(question + ' [Y/n] ').lower().startswith('n')
        else:
            return not input(question + ' [y/N] ').lower().startswith('y')

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

        origin_match = re.search(r'Fetch URL: (.+)', self.run('git remote show -n origin'))
        if origin_match:
            origin = origin_match.group(1)
            if origin.startswith('https://'):
                if self.yes_or_no('git_ssh', 'Using HTTPS origin ({}). Switch to ssh?'.format(origin), True):
                    extract_pattern = 'https://(.+?)/(.+?)/(.+?)(?:.git)?$'
                    domain, user, repo = re.match(extract_pattern, origin).groups()
                    new_origin = 'git@{}:{}/{}'.format(domain, user, repo)
                    self.run(['git', 'remote', 'set-url', 'origin', new_origin])

        status = self.run('git status --porcelain')
        if re.search(r'^\?\? ', status) or re.search(r'^\s*M ', status):
            print('Repository has uncommitted files:')
            print(re.sub('^##.+\n?', '', status))
            print('You may want to clean them up first.')

        sync_status = re.search(r'^## .+? \[(ahead|behind) (\d+)\]', self.run('git status --porcelain --branch'))
        if sync_status:
            direction, number = sync_status.groups(1)
            if self.yes_or_no('git_sync', '{} of remote by {} commits.. Perform sync now?'.format(direction.title(), number), True):
                self.run('git merge')
                self.run('git push')
            
if __name__ == '__main__':
    Supervisor().ensure_git()