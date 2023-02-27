# PyEnd

Python's significant [indentation](https://peps.python.org/pep-0666/) is a [horrible](https://www.quora.com/What-are-the-downsides-to-whitespace-indentation-rather-than-requiring-curly-braces) [thing](https://yinwang0.wordpress.com/2011/05/08/layout/) that [ruins](https://qr.ae/pr9Pxf) the [language](https://www.quora.com/Why-do-people-dislike-indented-programming-languages-when-they-indent-their-code-anyway) for [many](https://news.ycombinator.com/item?id=1463451
) [people](https://www.linkedin.com/pulse/why-python-indentation-sucks-what-can-done-spoiler-alert-mayank-verma).

It's now fixed.

PyEnd introduces `end` to mark the end of blocks:

```python
from pyend import end

if "tabs" > "spaces":
	print("∎")
end
```

## Why is that useful?

Because it is also a formatter. You can convert indentation-based code (both the file you are working on and the clipboard) into keyword-delimited code. You can then paste away and afterwards reformat your file automatically instead of manually. It should also be quite helpful for refactoring, when the code structure changes and everything has to be re-indented.

## Status

This project is still an experiment. Feel free to play around with it and give feedback but don't use it in production code. You may have noticed there are no unit tests yet. Formatting code (especially with significant indentation) is actually not so straight forward and can easily mess things up. That being said, the formatter does some validation in the end. The formatted code is tokenized again and compared to the tokenized original input.

## Installation

```
pip install pyend
```

## Hasn't this whole thing been done before?

In contrast to [pindent](https://svn.python.org/projects/python/trunk/Tools/scripts/pindent.py), it works with Python3 and in contrast to [pybrace](https://github.com/mayank-verma048/PyBrace) and [pybraces](https://timhatch.com/projects/pybraces/), the output is still valid Python.

## Does it stop there?

It sure does not! It also uses tabs instead of spaces for indentation. Because using tabs instead of spaces is much better. However, if you want to be wrong, you can set the `--convert-tabs-to-spaces-despite-tabs-being-objectively-better-than-spaces` flag, which will convert indentation tabs into 11 spaces. Should you not like 11 spaces for indentation and you would rather enforce your personal taste onto everyone else, you can set the `--use-this-many-spaces-per-tab-cuz-as-a-spacist-i-want-uniformity-but-i-dont-want-the-default` parameter to whatever your heart desires.

## Why are tabs better than spaces?

At the core of the spacecrafters' arguments lies the conviction that their pristine code must look the same everywhere. This idea is just doomed to failure. While a typical space users' code probably looks something like this on their 79 column console or on their printed handouts:

![space user code](https://raw.githubusercontent.com/mqnc/pyend/img/space_code.png)

the exact same code will render like this on my monitor:

![my code](https://raw.githubusercontent.com/mqnc/pyend/img/my_code.png)

so why even bother with indentation width consistency?

Furthermore, [Developers Who Use Spaces Make More Money Than Those Who Use Tabs](https://stackoverflow.blog/2017/06/15/developers-use-spaces-make-money-use-tabs/). This is because space invaders need higher monetary compensation to make up for the fact that developers who use tabs are happier in general because they make better life choices.

That should settle it.

## Does PyEnd fix all the bad decisions in Python's language design?

Unfortunately not. Empty blocks will still need a `pass`:

```python
if None:
	pass
end
```

Furthermore, `myList[0:5]` still absolutely counter-intuitively only goes up to `myList[4]` and there is also [this atrocity](https://www.geeksforgeeks.org/least-astonishment-and-the-mutable-default-argument-in-python/). But hey, it's a start!

## What about line breaks?

Line breaks are a [Pandora's box](https://journal.stuffwithstuff.com/2015/09/08/the-hardest-program-ive-ever-written/) that this project is not touching. You have to sprinkle the line breaks in manually (you're much better at this than any tool anyway), or you use another formatter on top of PyEnd.

## But in my project I have a variable named `end`. Am I forced to live under van Rossum's dictatorship then?

PyEnd only recognizes an `end` on an otherwise empty line (except for comments) as block end mark. Using `end` otherwise is a bit ugly as every block-ending `end` then becomes a reference to your variable but it is possible.

## This is a great project! You are very clever and handsome! Can you also do this for YAML?

Thanks but no. YAML is [screwed up beyond repair](https://en.wikipedia.org/wiki/YAML#Criticism), starting with its very funny name and not ending with its ambiguity. Use JSON. It has its [problems](https://seriot.ch/projects/parsing_json.html) as well but I feel they aren't really relevant in practice and I also just like it more 😌

## Disclosure

If I didn't consider Python to be a great language, I wouldn't invest so much time in this project. But significant indentation has been an absolute PITA and the urge to do something about it has been bugging me with every paste. I finally gave in.