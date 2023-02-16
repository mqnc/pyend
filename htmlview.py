import tokenize
import sys
import io
import hashlib
import html

def htmlize(src):

	# convert to string
	if type(src) == bytes:
		encoding = tokenize.detect_encoding(io.BytesIO(src).readline)[0]
		srcString = src.decode(encoding)
	else:
		srcString = src

	if srcString[-1] != "\n":
		srcString += "\n"


	# for converting (line, column) to char index
	lines = io.StringIO(srcString).readlines() + [""]
	lineOffsets = [0, 0]
	sum = 0
	for line in lines:
		sum += len(line)
		lineOffsets.append(sum)

	tokens = list(tokenize.generate_tokens(io.StringIO(srcString).readline))


	# collect white space info between tokens
	class WhiteSpace:
		def __init__(self, string):
			self.string = string
			self.type = WhiteSpace

		def __str__(self):
			return "WhiteSpace(" + repr(self.string) + ")"

	tokensAndWhitespaces = []

	lastTokenEnd = 0
	for token in tokens:
		l0, c0 = token.start
		tokenStart = lineOffsets[l0]+c0
		whiteSpace = srcString[lastTokenEnd:tokenStart]
		first = True
		for ws in whiteSpace.split("\\\n"):
			if first:
				first = False
			else:
				tokensAndWhitespaces.append(WhiteSpace("\\\n"))
			tokensAndWhitespaces.append(WhiteSpace(ws))
		tokensAndWhitespaces.append(token)
		l1, c1 = token.end
		lastTokenEnd = lineOffsets[l1]+c1

	# remove very first white space
	tokensAndWhitespaces = tokensAndWhitespaces[1:]

	def str2col(string):
		hash = hashlib.sha1(string.encode("utf-8")).digest()
		r = hex(hash[3] | 0x80)[2:]
		g = hex(hash[4] | 0x80)[2:]
		b = hex(hash[6] | 0x80)[2:]
		return f"#{r}{g}{b}"

	ostream = ["<div style='font-family:monospace'>"]
	for t in tokensAndWhitespaces:
		snip = t.string.replace("\t", "⊢−−⊣").replace(" ", "⎵").replace("\n", "↲<br>")
		if snip == "":
			snip=" "
		if t.type == WhiteSpace:
			typ = "WhiteSpace"
		else:
			typ = tokenize.tok_name[t.type]
		ostream.append(f"<span style='background-color:{str2col(str(t.type))}' title='{typ}'>{snip}</span>")
	ostream.append("</div>")

	return ''.join(ostream)

with open(sys.argv[1]) as fid:
	output = htmlize(fid.read())

with open(sys.argv[1] + ".html", "w") as fid:
	fid.write(output)