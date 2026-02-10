# OOP Course - Feb 2026 Materials

Materials for the Feb 2026 iteration of OOP.

- The specs for the mini-project are in [marketplace.md](marketplace.md), we'll work through it together.
- Assorted examples are in the [examples](examples/) folder
- A sample assignment is in [sample-oop-assignment.pdf](sample-oop-assignment.pdf).

The repository for this is: https://github.com/sg495/oop-course-2026-02


## Some Python books

- [The Big Book of Small Python Projects](https://nostarch.com/big-book-small-python-projects)
- [Impractical Python Projects](https://nostarch.com/impracticalpythonprojects)
- [Dead Simple Python](https://nostarch.com/dead-simple-python)
- [Object-Oriented Python](https://nostarch.com/object-oriented-python)

## Useful references

- [Official Python Documentation](https://docs.python.org/3/)
- [Time complexity for collection operations](https://wiki.python.org/moin/TimeComplexity)
- [The ``typing`` module](https://docs.python.org/3/library/typing.html)
- [The ``collections.abc`` module](https://docs.python.org/3/library/collections.abc.html)
- [Python's Data Model](https://docs.python.org/3/reference/datamodel.html)
- [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/)

## Visual Studio Code

You should install [VS Code](https://code.visualstudio.com/) and set it up for [Python](https://code.visualstudio.com/Docs/languages/python).
You should install the following extensions:

- the [`Python` extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
- the [`Python Debugger` extension](https://marketplace.visualstudio.com/items?itemName=ms-python.debugpy)
- the [`Mypy Type Checker` extension](https://marketplace.visualstudio.com/items?itemName=ms-python.mypy-type-checker)

A `pyproject.toml` file at the root of this repository instructs Mypy to run in [strict mode](https://mypy.readthedocs.io/en/stable/command_line.html#cmdoption-mypy-strict) using Python 3.14.

You might have to set the Python language server to `Pylance` in settings.
You might have to set Auto-Import Completions to true on the language menu in the bottom right of the VS Code window.

If you wish to select Unicode characters using the VS Code command line, you can do so by installing the [`Insert Unicode` extension](https://marketplace.visualstudio.com/items?itemName=brunnerh.insert-unicode).


## Command Line Tools

The [Mypy](https://github.com/python/mypy) static type-checker (in strict mode):

```py
mypy --strict <module>
```

The [Black](https://github.com/psf/black) code formatter:

```py
black <module>
```

The [Ruff](https://github.com/astral-sh/ruff) linter:

```py
ruff check <module>
```

```py
ruff format <module>
```

I have `mypy 1.19.1`, `black 26.1.0` and `ruff 0.15.0`.

Also worth mentioning are:

- the [`uv` package manager](https://docs.astral.sh/uv/), a stable project superior in most ways to `pip`.
- the [`ty` static type-checker](https://docs.astral.sh/ty/), a promising alpha stage project.



## Naming your local files

To avoid conflicts with the files pushed into this repository, make sure that your local working copies of files have names ending in `-local.py`, or that they are contained in folder with names ending in `-local`.
There are `.gitignore` rules set up to ignore such files and folders in commits.
