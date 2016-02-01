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

OBLIGATORY = object()

def ask(tag, question, default=OBLIGATORY):
    while True:
        response = input(question + ' ')
        if response:
            return response
        elif default is not OBLIGATORY:
            return default

def yes_or_no(tag, question, default):
    if default == True:
        return not input(question + ' [Y/n] ').lower().startswith('n')
    else:
        return not input(question + ' [y/N] ').lower().startswith('y')

def run(command, verbose=False):
    if verbose:
        print('  RUNNING {}'.format(command))
    return check_output(command, stderr=STDOUT).decode('utf-8')

def search(pattern, text):
    return re.search(pattern, text, re.MULTILINE)
    

here = Path('.')

def ensure_git():
    try:
        run('git status')
    except CalledProcessError:
        if yes_or_no('git_init', 'Not a git repo. Initialize one?', True):
            run('git init')
            run('git commit --allow-empty -m "Create repo"')
        else:
            return

    gitignore = here / '.gitignore'
    if not gitignore.exists():
        if yes_or_no('create_gitignore', 'Missing git ignore. Create one?', True):
            with gitignore.open('w') as f:
                f.write('*.pyc\n__pycache/')

    try:
        run('git fetch')
    except CalledProcessError:
        remote = ask('set_github', 'No remote set. Remote url (or none to skip):', None)
        if remote is not None:
            run(['git', 'remote', 'add', 'origin', remote])
            run('git push --set-upstream origin master')

    status = run('git status --porcelain')
    if search(r'^\?\? ', status) or search(r'^\s*M ', status):
        print('Repository has uncommitted files:')
        print(re.sub('^##.+\n?', '', status))
        print('You may want to clean them up first.')

    sync_status = search(r'^## .+? \[(ahead|behind) (\d+)\]', run('git status --porcelain --branch'))
    if sync_status:
        direction, number = sync_status.groups(1)
        if yes_or_no('git_sync', '{} of remote by {} commits.. Perform sync now?'.format(direction.title(), number), True):
            run('git merge')
            run('git push')

    #run('git pull')
    #run('git push origin master')

    #print(run('git status'))
            
if __name__ == '__main__':
    ensure_git()