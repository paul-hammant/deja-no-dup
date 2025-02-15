import os
import sys
import subprocess

def create_ignore_file(directory):
    with open(os.path.join(directory, '.deja-dup-ignore'), 'w') as f:
        pass  # Just create an empty file

def is_git_clean(directory):
    """Check if the git repository is clean and has no unpushed commits on any branch."""
    # Check for uncommitted changes using git status
    result = subprocess.run(
        f"git -C {directory} status --porcelain",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    changes = result.stdout.splitlines()
    changes = [change for change in changes if not change.endswith('.deja-dup-ignore')]
    if changes:
        return False
    # Check for unpushed commits on all branches without switching
    branches = os.popen(f"git -C {directory} for-each-ref --format='%(refname:short)' refs/heads/").read().splitlines()
    all_clean = True
    for branch in branches:
        result = subprocess.run(
            f"git -C {directory} rev-parse --abbrev-ref --symbolic-full-name {branch}@{{u}}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        upstream_branch = result.stdout.strip()
        if "fatal: bad revision 'HEAD'" in result.stderr:
            print(f"Warning: No commits in the branch {branch} at {directory}. Assuming dirty.")
            all_clean = False
        elif "fatal: no upstream configured for branch" in result.stderr:
            print(f"No upstream configured for branch {branch} in {directory}. Assuming dirty.")
            all_clean = False
        elif "fatal: unknown commit" in result.stderr:
            print(f"Unknown commit for branch {branch} in {directory}. Assuming dirty.")
            all_clean = False
    return all_clean

def find_ignorable_folders_within(dirpath):
    if dirpath.endswith("/.wine") or dirpath.endswith("/bottles"):
        # A world of no-permissions pain in there
        return
    listdir = []
    try:
        listdir = os.listdir(dirpath)
    except PermissionError:
        pass
    for dirname in listdir:
        full_path = os.path.join(dirpath, dirname)
        if os.path.isdir(full_path):
            dot_git_folder = os.path.join(full_path, '.git')
            if os.path.exists(dot_git_folder):
                if is_git_clean(full_path):
                    remote_url = os.popen(f"git -C {full_path} config --get remote.origin.url").read().strip()
                    last_path_part_of_dirpath = os.path.basename(os.path.dirname(full_path))
                    try:
                        with open(os.path.join(dirpath, 'git_backup_ignore_explanations.txt'), 'a') as f:
                            f.write(
                                f"This directory - {full_path} - is a clean git repository with no unpushed commits.\n")
                            f.write(f"We can safely ignore it during backup. To restore, use git clone or fetch.\n")
                            f.write(f"To clone: git clone {remote_url} {last_path_part_of_dirpath}\n\n")
                        create_ignore_file(full_path)
                        continue
                    except FileNotFoundError:
                        print("File not found - parent of " + full_path)
                    except PermissionError:
                        pass

                # Only mark these if a git checkout
                if dirname in ['bin', 'obj', 'dist']:
                    create_ignore_file(full_path)
                    continue

            # These could be at the root of a git checkout, OR deeper (multi-module)
            if dirname == 'build':
                if any(gradle_file in os.listdir(dirpath) for gradle_file in ['build.gradle', 'settings.gradle']):
                    create_ignore_file(full_path)
                    continue
            elif dirname == 'target':
                if 'pom.xml' in os.listdir(dirpath) or 'Cargo.toml' in os.listdir(dirpath):
                    create_ignore_file(full_path)
                    continue

            find_ignorable_folders_within(full_path)


if __name__ == "__main__":

    if len(sys.argv) != 1 or (len(sys.argv) > 1 and sys.argv[1] == '--help'):
        print("Usage: python deja-dup-ignores.py")
        print("This slims down a deja-dup backup to ignore dirs that could be recreated")
        sys.exit(1)

    home_dir = os.path.expanduser("~")

    #We are going to recreate and of `git_backup_ignore_explanations` in subfolders, if needed
    for dirpath, _, filenames in os.walk(home_dir):
        for filename in filenames:
            if filename == 'git_backup_ignore_explanations.txt' or filename == '.deja-dup-ignore':
                    os.remove(os.path.join(dirpath, filename))

    pkg_cache = os.path.join(home_dir, ".gradle/caches/modules-2/files-2.1")
    if os.path.exists(pkg_cache):
        create_ignore_file(pkg_cache)

    pkg_cache = os.path.join(home_dir, ".m2/repository")
    if os.path.exists(pkg_cache):
        create_ignore_file(pkg_cache)

    pkg_cache = os.path.join(home_dir, ".cargo/registry")
    if os.path.exists(pkg_cache):
        create_ignore_file(pkg_cache)

    find_ignorable_folders_within(home_dir)

    for dirpath, _, filenames in os.walk(home_dir):
        for filename in filenames:
            if filename == 'git_backup_ignore_explanations.txt':
                print("git_backup_ignore_explanations.txt in " + dirpath)
            if filename == '.deja-dup-ignore':
                print(".deja-dup-ignore in " + dirpath)
