
from pyend import fmt

if 1 \
		and 2:
	pass

if (1
		and 2):
	pass

if (1
	and 2
):
	pass

if (1 \
		and 2):
	pass

if 1:
	if 2:
		if 3:
			3
0

if 1:
	if 2:
		if 3:
			3

0

if 1:
	if 2:
		if 3:
			3
	1

if 1:
	if 2:
		if 3:
			3

	1

x = [
	[
		1
	]
]

x = [[
		1
	]
]

x = [
	[
		1
	]]

x = [[
	1
]]

x = +1
x = 1 + 1

with open(__file__) as me:
	src = me.read()

with open(__file__ + ".formatted.py", "w") as out:
	out.write(fmt(src))

fmted = fmt(src)

assert src == fmted
