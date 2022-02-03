# `assert-changelog` pre commit hook

`assert-changelog` is a [`pre-commit` hook](https://pre-commit.com/) for Python projects that attempts to find mentions of untracked or unstaged work in your CHANGELOG.
`assert-changelog` leverages the predictable format of the [Keep a Changelog style](https://keepachangelog.com/) and a simple Sphinx-like markup (eg. "hoot/client/test.py" is \`hoot.client.test\`) to identify whether your CHANGELOG refers to untracked or uncommitted files in your repository.

Python modules are identified with `pkgutil.walk_packages`, and mapped to the output of `git ls-files`.
The CHANGELOG is then parsed to determine whether any backtick quoted phrases make reference to a Python module that has been mapped to an untracked or unstaged file.

The hook is in early development and will need a lot of fiddling to cover tricky use-cases that are almost sure to show up.

## Configure

Add the following block to your .pre-commit-config.yaml:

```
-  repo: https://github.com/SamStudio8/pre-commit-assert-changelog
   rev: 0f0fd2fe45651c3fb4ead6f3d08d881195ea77dc
   hooks:
   -   id: assert-changelog-version
       args: [--version-mod=<mypackage>/version.py]
   -   id: assert-changelog-contents
       args: [--backtick-prefixes=<mypackage>,--package-dir-name=<mypackage>,--exclude-previous]
```

* You will need to replace `<mypackage>` with the directory name that contains the top-level package of your Python repo.

## Example

Assuming a Python project layout:

```
my-app/
├─ hoot/             # --package-dir
│  ├─ __init__.py
│  ├─ client.py
│  ├─ version.py     # --version-mod
│  ├─ ...
|
├─ CHANGELOG.md
├─ ...
```

You will need to configure `assert-changelog` with:

* `--version-mod=hoot/version.py`
* `--backtick-prefixes=hoot`, `--package-dir=hoot`


## CHANGELOG format

* Follow the [keepachangelog style](https://keepachangelog.com/) conventions
* Code files and modules should be referred to between backticks, for example:

```
# 1.0.0
* Released new `hoot.client.HootClient` to better support users who are owls
```

* Only backtick strings that begin with an allowed prefix (configured with `--backtick-prefixes`) will be screened against untracked and unstaged code files

## Version module format

Your version module should be formatted:

```
__VERSION__ = "x.y.z"
```
