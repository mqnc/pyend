# PyEnd

The upcoming release of Python4.0 will introduce a major syntax change: an `end` keyword to signal the end of a code block.

```python
if meaningOfLife is not None:
    print("much rejoicing")
end
```

PyEnd brings the `end` keyword to Python3 already, allowing you to start migrating your codebase.

## In a Nutshell
An `end` keyword for ending blocks has the following advantages:

* It eliminates every kind of `IndentationError` and `TabError`, which often cause confusion for beginners.
* Code can easily be automatically re-indented. This is especially helpful for refactoring and when copying code from other sources with different coding guidelines.
* The structure of deeply nested code blocks becomes more obvious.
* Parsing (specifically tokenizing) becomes simpler and slightly faster, as there is no need for recognizing the pseudo tokens `INDENT` and `DEDENT`.
* The Python grammar can completely be expressed by a PEG, eliminating the need for an extra tokenizer entirely.
* No `pass`.

These are the considered disadvantages:

* It will take some getting used to.
* Source files will require around 15% more lines of code.
* The `end` parameter in `print` has to be renamed.

## Discussion
When Python was first introduced in the 90s, significant indentation contributed significantly to its popularity. Forcing developers to write properly indented code and the tidy syntax of Python in general resulted in more readable code and overall cleaner codebases. This made Python projects more pleasant to work with, giving it an edge over other languages, despite its tremendous shortcomings in performance.

However, with the rise of modern IDEs that have code formatters plugged in, significant indentation has turned into an obstruction. While bracketed or keyword-delimited languages can easily be formatted automatically (including indentation), it is impossible for a formatter to know where a block ends, if it is not already properly indented. As mentioned in the nutshell, manual re-indentation is especially cumbersome when restructuring code during refactoring or when copying code from other sources. Especially because Python allows both tabs and different amounts of spaces for indentation.

The Python core development team has experimented with an `end` keyword in test projects for quite some time now, performing cold hard measurements. While writing new code on a blank slate is slightly slower (around 4%) just from typing all the `end`s, shaping and evolving existing code becomes significantly faster (10-20%). As the latter quickly becomes the main job even in small projects, it was decided to bring an `end` to Python.

## Installation
```
pip install pyend
```

## Usage
```
pyend [-h] [-o OUT] [-c] [-e] [-i] [-s] [-n] [filename]

positional arguments:
  filename              input file name

options:
  -h, --help            show this help message and exit
  -o OUT, --out OUT     output file name, input file is overwritten if omitted
  -c, --clipboard       use clipboard content as input (and output if no output file is specified)
  -e, --insert-end      insert end marks based on indentation
  -i, --ignore-indent   ignore indentation and format code only based on end marks
  -s, --strip-end       remove all end marks
  -n, --end-is-none     use 'end = None' instead of 'from pyend import end'
```

