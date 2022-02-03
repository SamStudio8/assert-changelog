import os
import argparse
import sys
import re
import subprocess
import pkgutil
import keepachangelog
import textwrap


def changelog_to_dict(changelog_fp, show_unreleased=True):
    return keepachangelog.to_dict(changelog_fp, show_unreleased=show_unreleased)


def wrap_git_cmd(cmd_l):
    # NOTE Use universal_newlines=True to force Popen to return str over bytes to avoid working out which decode to use
    p = subprocess.Popen(
        cmd_l, stdout=subprocess.PIPE, universal_newlines=True
    )
    out, err = p.communicate()
    return out.split("\n")[:-1]  # Remove last newline


def get_untracked_files():
    return wrap_git_cmd(["git", "ls-files", "--others", "--exclude-standard"])


def get_cached_files():
    return wrap_git_cmd(["git", "ls-files", "--cached"])


def get_staged_files():
    return wrap_git_cmd(["git", "diff", "--staged", "--name-only"])


# NOTE pre-commit stashes unstaged modified files so this command is a bit useless
def get_unstaged_modified_files():
    return wrap_git_cmd(["git", "ls-files", "--modified"])


# https://stackoverflow.com/a/1310912/
# https://stackoverflow.com/a/1707786/
def get_python_module_names(package_dir_name):

    modules = set([])

    # Add empty string to sys path to allow prefix to work and correctly
    # import subpackages, empty string on the sys.path is standard behaviour
    # when the script dir is not available:
    # > If the script directory is not available (e.g. if the interpreter is
    # > invoked interactively or if the script is read from standard input),
    # > path[0] is the empty string
    # See https://docs.python.org/3/library/sys.html#sys.path
    # See https://bugs.python.org/issue33210 and
    sys.path.append("")
    for importer, modname, ispkg in pkgutil.walk_packages(
        [f"{package_dir_name}/"], prefix=f"{package_dir_name}."
    ):
        if not ispkg:  # actual modules only
            modules.add(modname)

    return modules


def assert_version(args):

    with open(args.version_mod) as version_fh:
        version = (
            version_fh.readline().strip().split()[-1].replace('"', "").replace("'", "")
        )

    version_in_header = False
    with open(args.changelog) as changelog_fh:
        for line in changelog_fh:
            # Just assume any line starting with a # is a possible version header
            if line.startswith("#"):
                if version in line:
                    version_in_header = True

    if not version_in_header:
        sys.stderr.write(
            f"Entry for version {version} not found in CHANGELOG ({args.changelog})\n"
        )
        return 1

    return 0


def assert_contents(args):

    changelog_assert_report = []  # struct to hold info to report to the user later

    # Get a list of python files that have not been committed to the repo
    # and make them look like python module paths
    untracked_files = get_untracked_files()
    untracked_modules_map = {
        fp.replace("/", ".").replace(".py", ""): fp
        for fp in untracked_files
        if fp.lower().endswith(".py")
    }

    # Find the set of files that are tracked in the repo but have not been staged
    # as these files may be modules that potentially contain uncommitted code
    # NOTE this will not be able to handle a case where a git add --patch does
    # not stage a change referenced in the changelog, without reading the actual patch
    cached_files = set(get_cached_files())
    staged_files = set(get_staged_files())
    potentially_unstaged_files = cached_files - staged_files
    potentially_unstaged_modules_map = {
        fp.replace("/", ".").replace(".py", ""): fp
        for fp in potentially_unstaged_files
        if fp.lower().endswith(".py")
    }

    # Use pkgutil to enumerate the full list of module paths in the package
    full_module_set = get_python_module_names(args.package_dir_name)

    changelog = changelog_to_dict(
        args.changelog, show_unreleased=not args.exclude_unreleased
    )
    latest_version = keepachangelog.to_sorted_semantic(changelog.keys())[-1][
        0
    ]  # will exclude unreleased, returns tuple

    for changelog_version, changelog_data in changelog.items():

        if args.exclude_previous and (
            (changelog_version != latest_version)
            and (changelog_version != "unreleased")
        ):
            # Bail if we only want to read the latest version and this is not
            # the latest version or unreleased (--exclude-unreleased prevents it
            # appearing in the struct here)
            continue

        # Iterate over the k:v map for this changelog block
        for change_k, change_v in changelog_data.items():
            if change_k in ["version", "release_date", "semantic_version"]:
                # Skip keys we are not interested in
                continue

            # If we haven't skipped the key, this must be a change log category
            # Each entry represents a line from the changelog entry for a given version
            # Now we're at the good stuff
            for changelog_entry in change_v:
                for prefix in args.backtick_prefixes.split(","):

                    # Check and captures cases where it looks like the changelog
                    # refers to a package prefix
                    matches = re.findall(f"`({prefix}[^`]*)`", changelog_entry)
                    for match in matches:
                        # Screen matched module path for against known untracked modules
                        if match in untracked_modules_map.keys():
                            changelog_assert_report.append(
                                {
                                    "ref": match,
                                    "entry": changelog_entry,
                                    "msg": f"{untracked_modules_map[match]} is untracked",
                                    "version": changelog_version,
                                }
                            )
                            continue

                        # Try and check match against potentially unstaged things
                        for known_module in full_module_set:
                            # Screen list of known modules against matches with `in`
                            # to detect cases where classes or other substructures
                            # of a module are being referred to
                            # eg. known_module IN match
                            #     hoot.client  IN hoot.client.HootClient
                            if (
                                known_module in match
                                and known_module
                                in potentially_unstaged_modules_map.keys()
                            ):
                                # Matched module path is part of a known_module, and is unstaged
                                changelog_assert_report.append(
                                    {
                                        "ref": match,
                                        "entry": changelog_entry,
                                        "msg": f"{potentially_unstaged_modules_map[known_module]} is not staged",
                                        "version": changelog_version,
                                    }
                                )

    if len(changelog_assert_report) > 0:
        sys.stderr.write("References to uncommitted code detected: \n")
        for ref in changelog_assert_report:
            wrap = "\n    ".join(textwrap.wrap(ref["entry"]))
            sys.stderr.write(f"\n  * ({ref['version']}) {wrap}\n")
            sys.stderr.write(f"    ...but {ref['msg']}\n")
        sys.stderr.write(
            "\nCommit these files or update the CHANGELOG to remove the references to permit a commit.\n"
        )
        return 1
    return 0


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--changelog", default="CHANGELOG.md")

    action_parser = parser.add_subparsers()

    version_parser = action_parser.add_parser("version")
    version_parser.add_argument(
        "--version-mod", required=True, help="path to file containing __VERSION__ def"
    )
    version_parser.set_defaults(func=assert_version)

    contents_parser = action_parser.add_parser("contents")
    contents_parser.add_argument(
        "--backtick-prefixes", help="comma delimited list of prefixes"
    )
    contents_parser.add_argument(
        "--package-dir-name", help="top level package dir for pkgutil"
    )
    contents_parser.add_argument(
        "--exclude-unreleased", action="store_true", default=False
    )
    contents_parser.add_argument(
        "--exclude-previous", action="store_true", default=False
    )
    contents_parser.set_defaults(func=assert_contents)

    args = parser.parse_args()

    if not os.path.exists(args.changelog):
        sys.stderr.write(f"Changelog could not be found at {args.changelog}\n")
        sys.stderr.write(
            "Fix the --changelog path, or create a changelog with Keep a Changelog formatting to permit a commit!\n"
        )
        return 1

    if hasattr(args, "version_mod") and not os.path.exists(args.version_mod):
        sys.stderr.write(f"Version module could not be found at {args.version_mod}\n")
        sys.stderr.write(
            "Fix the --version-mod path, or create a module with __VERSION__ to permit a commit!\n"
        )
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
