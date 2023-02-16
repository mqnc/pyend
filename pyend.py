import tokenize
import io
import re
import keyword

end = None

def fmt(src, check = True, debug = False):

	blockEndMarker = "end"

	if debug:
		blockIndent = "␎"
		blockDedent = "␏"
		substitute = "␚"
		escape = "␛"
	else:
		blockIndent = "\N{SHIFT IN}"
		blockDedent = "\N{SHIFT OUT}"
		substitute = "\N{SUBSTITUTE}"
		escape = "\N{ESCAPE}"

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

	if debug:
		for t in tokensAndWhitespaces:
			print(t)

	# find where multiple opening and corresponding closing brackets are on the same line
	# so we can coalesce them (indent the code in between only once)
	bracketStack = [None]
	corresponding = {}
	outer = {}
	coalesce = {}

	for t in tokensAndWhitespaces:
		if type(t) == tokenize.TokenInfo:
			if t.type == tokenize.OP and t.string in "([{":
				outer[t] = bracketStack[-1]
				bracketStack.append(t)
			elif t.type == tokenize.OP and t.string in "}])":
				if len(bracketStack) > 1:
					corresponding[t] = bracketStack.pop()
					corresponding[corresponding[t]] = t
				else:
					corresponding[t] = None

	bracketStack = [None]
	for t in reversed(tokensAndWhitespaces):
		if type(t) == tokenize.TokenInfo:
			if t.type == tokenize.OP and t.string in "}])":
				outer[t] = bracketStack[-1]
				bracketStack.append(t)
			elif t.type == tokenize.OP and t.string in "([{":
				if len(bracketStack) > 1:
					bracketStack.pop()

	for t in tokensAndWhitespaces:
		if (
			type(t) == tokenize.TokenInfo
			and t.type == tokenize.OP
			and t.string in "([{"
			and outer[t] is not None
			# bracket and opening surrounding bracket on same line
			and t.start[0] == outer[t].start[0]
			# same with their corresponding closing brackets
			and corresponding[t].start[0] == outer[corresponding[t]].start[0]
		):
			coalesce[t] = True
			coalesce[corresponding[t]] = True

	# main indentation and white space pass
	ostream = []
	stringsAndComments = []
	indentLevel = 0
	bracketLevel = 0
	lastToken = WhiteSpace(None)
	isInfix = {}
	blockStack = []

	for i, t in enumerate(tokensAndWhitespaces):
		if type(t) == tokenize.TokenInfo:
			if t.type == tokenize.ENCODING:
				pass
			elif t.type == tokenize.COMMENT or t.type == tokenize.STRING:
				ostream.append(substitute)
				stringsAndComments.append(t.string)
			elif t.type == tokenize.INDENT:
				ostream.append(blockIndent)
				ostream.append("\t")
				indentLevel += 1
				# find the token that caused this indent: the first NAME after the last NEWLINE
				j = i
				while j>0 and tokensAndWhitespaces[j].type != tokenize.NEWLINE:
					j -= 1
				while j<i and tokensAndWhitespaces[j].type != tokenize.NAME:
					j += 1
				if j == i:
					blockStack.append(None)
				else:
					blockStack.append(tokensAndWhitespaces[j].type)
			elif t.type == tokenize.DEDENT:
				indentLevel -= 1

				# remove one tab
				k = -1
				while ostream[k] == blockDedent:
					k -= 1
				if len(ostream[k]) > 0 and ostream[k][-1] == "\t":
					ostream[k] = ostream[k][:-1]

				# insert block end marker
				if blockEndMarker is not None:
					# find next meaningful token and pass if it is already an implicit block end marker
					j = i+1
					while j < len(tokensAndWhitespaces) and tokensAndWhitespaces[j].type in [
						WhiteSpace, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.COMMENT
					]:
						j += 1
					if tokensAndWhitespaces[j].string in ["elif", "else", "catch", "finally"]:
						pass
					elif len(blockStack) > 0 and blockStack[-1] == "case":
						pass
					else:
						k = len(ostream)
						while (
							len(ostream[k-1]) == 0
							or ostream[k-1] in [blockDedent, "\n"]
							or ostream[k-1].count("\t") == len(ostream[k-1])
						):
							k -= 1
						ostream.insert(k, "\n" + "\t" * indentLevel + blockEndMarker)

				blockStack.pop()

				ostream.append(blockDedent)
			elif t.type == tokenize.OP and t.string in "([{":
				ostream.append(t.string)
				bracketLevel += 1
				if t not in coalesce:
					indentLevel += 1
			elif t.type == tokenize.OP and t.string in "}])":
				bracketLevel -= 1
				if t not in coalesce:
					indentLevel -= 1
				ostream.append(t.string)
			elif t.type == tokenize.NEWLINE or t.type == tokenize.NL:
				ostream.append("\n")
				ostream.append("\t" * indentLevel)
			elif t.type == tokenize.OP and t.string in ["+", "-"]:
				if lastToken.string in ["True", "False", "None", ")", "]", "}", "..."] \
						or lastToken.type in [tokenize.NAME, tokenize.NUMBER, tokenize.STRING]:
					isInfix[t] = True
				else:
					isInfix[t] = False
				ostream.append(t.string)
			else:
				ostream.append(t.string)

			lastToken = t
		elif type(t) == WhiteSpace:
			if t.string == "\\\n":
				ostream.append(t.string)
				ostream.append("\t" * indentLevel)
				if bracketLevel <= 0:
					ostream.append("\t")
			else:
				if i > 0:
					prv = tokensAndWhitespaces[i-1]
				else:
					prv = WhiteSpace(None)
				if i < len(tokensAndWhitespaces) - 1:
					nxt = tokensAndWhitespaces[i+1]
				else:
					nxt = WhiteSpace(None)

				noSpaceAround = [tokenize.INDENT, tokenize.DEDENT, tokenize.NEWLINE, tokenize.NL, tokenize.ENDMARKER]

				if len(prv.string) > 0 and prv.string[-1] in ["(", "[", "{", ".", ":", "~", "\t", "\n"] \
						or prv.string == "**" \
						or prv.type in noSpaceAround:
					pass
				elif len(nxt.string) > 0 and nxt.string[0] in [")", "]", "}", ".", ",", ":", ";", "\t", "\n"] \
						or nxt.string == "**" \
						or nxt.type in noSpaceAround:
					pass
				elif (
					(prv.type == tokenize.NAME or prv.type == tokenize.NUMBER or prv.string in [")", "]", "..."])
					and prv.string not in keyword.kwlist
					and nxt.string in ["(", "["]
				):
					pass
				elif prv.type == tokenize.OP and prv.string in ["+", "-"] and isInfix[prv] is False:
					pass
				else:
					ostream.append(" ")

	interRep = "".join(ostream)
	if debug:
		print(ostream)
		print(interRep)

	# corrections

	# remove 1 tab where the line starts with a closing bracket
	interRep = re.sub(r"\t([\)\]}])", r"\1", interRep)

	# remove whitespaces from empty lines
	interRep = re.sub(r"\t*\n", r"\n", interRep)

	# find "Continuation line with same indent as next logical line" and solve with further indentation
	def countTabs(s):
		n = 0
		for i in range(len(s)):
			if s[i] == "\t":
				n += 1
			elif s[i] in [blockIndent, blockDedent]:
				pass
			else:
				break
		return n

	lines = interRep.split("\n")

	for i, line in enumerate(lines):
		if len(line) > 0 and line[0] == blockIndent:
			tabs = countTabs(line)
			if countTabs(lines[i-1]) == tabs:
				j = i-1
				while j > 0 and countTabs(lines[j]) >= tabs:
					lines[j] = "\t" + lines[j]
					j -= 1

	interRep = "\n".join(lines)

	# remove indentation markers
	if not debug:
		interRep = re.sub("[" + blockIndent + blockDedent + "]", "", interRep)

	# put strings and comments back
	interRep = interRep.replace("%", escape)
	interRep = interRep.replace(substitute, "%s")
	interRep = interRep % tuple(stringsAndComments)
	interRep = interRep.replace(escape, "%")

	if check and not debug:
		compareTokens = list(tokenize.generate_tokens(io.StringIO(interRep).readline))
		for t1, t2 in zip(tokens, compareTokens):
			assert t1.type == t2.type
			assert t1.string == t2.string
		assert len(tokens) == len(compareTokens)

	if debug:
		interRep = interRep.replace("\t", "⊢−−⊣").replace(" ", "⎵")

	return interRep


if __name__ == "__main__":
	import argparse
	parser = argparse.ArgumentParser( prog = "pyend",
        description = "format python files and insert block end markers")

	parser.add_argument("filename")
	parser.add_argument("-d", "--debug", action="store_true")
	parser.add_argument("-o", "--out")

	args = parser.parse_args()

	with open(args.filename) as inFile:
		src = inFile.read()

	if args.out is not None:
		out = args.out
	elif args.debug:
		out = args.filename + ".fmt.dbg"
	else:
		out = args.filename

	with open(out, "w") as outFile:
		outFile.write(fmt(src, blockEndMarker = "end", debug = args.debug, check = False))
