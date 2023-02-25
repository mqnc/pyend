# PyEnd

Python's significant indentation is a [horrible](https://www.quora.com/What-are-the-downsides-to-whitespace-indentation-rather-than-requiring-curly-braces) thing that [ruins](https://qr.ae/pr9Pxf) the language for [many](https://news.ycombinator.com/item?id=1463451
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

Because it is also a formatter. You can convert indentation-based code (both the file you are working on as well as the clipboard) into keyword-delimited code. You can then paste away and afterwards reformat your file automatically instead of manually.

## Hasn't this been done before?

In contrast to [pindent](https://svn.python.org/projects/python/trunk/Tools/scripts/pindent.py) it works with Python 3 and in contrast to [pybrace](https://github.com/mayank-verma048/PyBrace) and [pybraces](https://timhatch.com/projects/pybraces/), the output is still valid Python code.

## Does it stop there?

It sure does not! It also uses tabs instead of spaces for indentation. Because using tabs instead of spaces is much better. However, if you hold the opinion that your pristine code should look the same everywhere, you can set the `--convert-tabs-to-spaces-despite-tabs-being-objectively-better-than-spaces` flag, which will convert indentation tabs into 11 spaces.

## Does it fix all the bad decisions in Python's language design?

Unfortunately not. Empty blocks will still need a `pass`:

```python
if None:
	pass
end
```

Furthermore, `myList[0:5]` still absolutely counter-intuitively only goes up to `myList[4]` and there is also [this atrocity](https://www.geeksforgeeks.org/least-astonishment-and-the-mutable-default-argument-in-python/).

## But in my project I have a variable named `end`. Am I forced to live under van Rossum's dictatorship then?

PyEnd only recognizes an `end` on an otherwise empty line (except for comments) as block end mark. It is a bit ugly as `end` then becomes a reference to your variable but what can we do about it.

## This is a great project! You are very clever and handsome! Can you also do this for YAML?

Thanks but no. YAML is [screwed up beyond repair](https://en.wikipedia.org/wiki/YAML#Criticism), starting with its very funny name and not ending with its ambiguity. Use JSON. It has its [problems](https://seriot.ch/projects/parsing_json.html) as well but I like it more 😌

## Disclosure

If I didn't consider Python to be a great language, I wouldn't invest so much time into this project. But this issue has been an absolute PITA and the urge to do something about it has been bugging me with every paste. I finally gave in.