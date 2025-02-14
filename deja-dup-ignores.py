import os
import sys
import shutil
import subprocess

def create_ignore_file(directory):
    ignore_file_path = os.path.join(directory, '.deja-dup-ignore')
    with open(ignore_file_path, 'w') as f:
        pass  # Just create an empty file

def is_git_clean(directory):
    """Check if the git repository is clean and has no unpushed commits on any branch."""
    # Check for uncommitted changes
    result = subprocess.run(
        f"git -C {directory} diff-index --quiet HEAD --",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if result.returncode != 0:
        if "fatal: bad revision 'HEAD'" in result.stderr:
            print(f"Warning: No commits in the repository at {directory}. Assuming dirty.")
        else:
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
            all_clean = False
    return all_clean

def find_ignorable_folders_within(root_dir):
    def visit_directory(dirpath):
        dot_git_folder = os.path.join(dirpath, '.git')
        if os.path.exists(dot_git_folder):
            if is_git_clean(dirpath):
                parent_dir = os.path.dirname(os.path.dirname(dirpath))
                explanation_file = os.path.join(parent_dir, 'git_backup_ignore_explanations.txt')
                remote_url = os.popen(f"git -C {dirpath} config --get remote.origin.url").read().strip()
                last_path_part_of_dirpath = os.path.basename(os.path.dirname(dirpath))
                with open(explanation_file, 'a') as f:
                    f.write(f"This directory - {dirpath} - is a clean git repository with no unpushed commits.\n")
                    f.write(f"We can safely ignore it during backup. To restore, use git clone or fetch.\n")
                    f.write(f"To clone: git clone {remote_url} {last_path_part_of_dirpath}\n\n")
                create_ignore_file(parent_dir)
                return

        # Not a clean Git folder wholly excluded
        for dirname in os.listdir(dirpath):
            full_path = os.path.join(dirpath, dirname)
            if os.path.isdir(full_path):
                if ("/.local/" in full_path or "/.cache" in full_path or "/.m2/" in full_path or "/.gradle/" in full_path
                        or "/.cargo/" in full_path or "/.jekyll-cache/" in full_path or "/.var/" in full_path
                        or "/.npm/" in full_path):
                    continue
                print("b> " + dirpath + " -> " + str(dirname))
                if dirname in ['bin', 'obj', 'dist']:
                    create_ignore_file(full_path)
                elif dirname == 'build':
                    if any(gradle_file in os.listdir(dirpath) for gradle_file in ['build.gradle', 'settings.gradle']):
                        create_ignore_file(full_path)
                elif dirname == 'target':
                    if 'pom.xml' in os.listdir(dirpath) or 'Cargo.toml' in os.listdir(dirpath):
                        create_ignore_file(full_path)
                visit_directory(full_path)

    visit_directory(root_dir)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python deja-dup-ignores.py <directory>")
        print("This slims down a deja-dup backup to ignore dirs that could be recreated")
        sys.exit(1)

    root_directory = sys.argv[1]
    # We are going to recreate and of `git_backup_ignore_explanations` in subfolders, if needed
    # for dirpath, _, filenames in os.walk(root_directory):
    #     for filename in filenames:
    #         if filename == 'git_backup_ignore_explanations.txt':
    #             os.remove(os.path.join(dirpath, filename))
    find_ignorable_folders_within(root_directory)
    # for dirpath, _, filenames in os.walk(root_directory):
    #     for filename in filenames:
    #         if filename == 'git_backup_ignore_explanations.txt':
    #             print("git_backup_ignore_explanations.txt in " + str(os.path.join(dirpath, filename)))
    #         if filename == '.deja-dup-ignore':
    #             print(".deja-dup-ignore in " + str(os.path.join(dirpath, filename)))
