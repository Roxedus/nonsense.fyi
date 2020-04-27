import os
import shutil

import git

ignore_dirs = [".git", "env", ".vscode", "temp", ".github"]
changed = []
foo = {}


for elem in os.listdir(os.getcwd()):
    if os.path.isdir(os.path.abspath(elem)):
        if elem in ignore_dirs:
            continue
        if os.path.exists(os.path.abspath(elem) + "/.gist"):
            repoName = open(os.path.abspath(elem) + "/.gist", "r").read()
            foo[repoName] = {'path': elem}

for gist, post in foo.items():
    msg = ""
    src = post["path"]
    dst = os.getcwd() + "/temp/" + gist.split("/")[1]
    cloned_repo = git.Repo.clone_from(
        f"https://{os.environ['GIT_USERNAME']}:{os.environ['GIT_PASSWORD']}@gist.github.com/{gist.split('/')[1]}.git", dst)
    author = git.Actor(os.environ['GIT_USERNAME'], os.environ['GIT_EMAIL'])
    committer = git.Actor(os.environ['GIT_USERNAME'], os.environ['GIT_EMAIL'])

    for filename in os.listdir(dst):
        file_path = os.path.join(dst, filename)
        try:
            if ".git" in file_path:
                continue
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

    for item in os.listdir(src):
        if item == ".gist":
            continue
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks=False, ignore=None)
        else:
            shutil.copy2(s, d)

    deleted = []
    added = []
    renamed = []
    modified = []

    for unt in cloned_repo.untracked_files:
        cloned_repo.index.add([unt])

    for diff_added in cloned_repo.head.commit.diff(None).iter_change_type('A'):
        cloned_repo.index.add([diff_added.a_path])
        added.append(diff_added.a_path)

    for diff_deleted in cloned_repo.head.commit.diff(None).iter_change_type('D'):
        cloned_repo.index.remove([diff_deleted.a_path])
        deleted.append(diff_deleted.a_path)

    for diff_renamed in cloned_repo.head.commit.diff(None).iter_change_type('R'):
        cloned_repo.index.remove([diff_renamed.rename_from])
        cloned_repo.index.add([diff_renamed.rename_to])
        renamed.append(diff_renamed.rename_to)

    for diff_modified in cloned_repo.head.commit.diff(None).iter_change_type('M'):
        cloned_repo.index.add([diff_modified.a_path])
        modified.append(diff_modified.a_path)

    if added:
        msg += f"Added {', '.join(added)}\n"
    if deleted:
        msg += f"Deleted {', '.join(deleted)}\n"
    if renamed:
        msg += f"Renamed {', '.join(renamed)}\n"
    if modified:
        msg += f"Modified {', '.join(modified)}\n"

    cloned_repo.index.commit(
        f"{msg}Automated by repo-to-gist sync", author=author, committer=committer)

    if (added or deleted or renamed or modified):
        print(cloned_repo.head.commit.message)

        cloned_repo.remote(name="origin").push()
