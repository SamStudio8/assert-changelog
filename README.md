# pre-commit-assert-changelog

pre-commit-assert-changelog is a `pre-commit` hook that attempts to find mentions of untracked or unstaged work in your CHANGELOG.
It assumes your source files end with `.py` so is limited to Python project, and you will need to be using a CHANGELOG formatted with the [keepachangelog style](https://keepachangelog.com/).
The hook is in early development and will need a lot of fiddling.

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

You will need to configure `pre-commit-assert-changelog` with:

* `--version-mod=hoot/version.py`
* `backtick-prefixes=hoot`, `--package-dir=hoot`


## CHANGELOG format

* Follow the [keepachangelog style](https://keepachangelog.com/) conventions
* Code files and modules should be referred to between backticks, for example:

```
# 1.0.0
* Released new `hoot.client.HootClient` to better support users who are owls
```

## Version module format

Your version module should be formatted:

```
__VERSION__ = "x.y.z"
```
