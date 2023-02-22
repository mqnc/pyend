from tokenize import generate_tokens, detect_encoding, tok_name, \
	NAME, NUMBER, STRING, OP, INDENT, DEDENT, NEWLINE, NL, COMMENT, ENCODING, ENDMARKER
import io
import keyword

end = None

class Line:
	__slots__ = ("breakBefore", "tokens", "logicalIndent", "opticalIndent")
	def __init__(self, breakBefore):
		self.breakBefore = breakBefore
		self.tokens = []
		self.logicalIndent = 0
		self.opticalIndent = 0
	def __repr__(self):
		return repr(self.tokens)

class Token:
	__slots__ = ("type", "srcString", "newString", "originalLine", "line")
	def __init__(self, type, srcString, origLine=None):
		self.type = type
		self.srcString = srcString
		self.newString = srcString
		self.originalLine = origLine
		self.line = None
	def __repr__(self):
		return self.srcString

class ScopeToken(Token):
	__slots__ = ("corresponding", "outer", "blockHead", "coalesce")
	def __init__(self, *args, **kwargs):
		super(ScopeToken, self).__init__(*args, **kwargs)
		self.corresponding = None # corresponding opening/closing token
		self.outer = None # for opening tokens, the opening token one level higher
		self.coalesce = False # for brackets, whether they don't need extra indentation
		self.blockHead = None # for indents the token at the start of the block

WHITESPACE = -1
ESCAPED_NL = -2


def fmt(src, insertEnd = True, validate = True, debug = False):

	blockEndMarker = "end" # has to be a single token to work
	# (will otherwise not be categorized as implicit block-end-marker when formatting already formatted code)

	# convert to string
	if type(src) == bytes:
		encoding = detect_encoding(io.BytesIO(src).readline)[0]
		srcString = src.decode(encoding)
	else:
		srcString = src

	# always end with \n
	if srcString[-1] != "\n":
		srcString += "\n"

	# for converting (line, column) to char index
	inputLines = io.StringIO(srcString).readlines() + [""]
	lineOffsets = [0, 0]
	sum = 0
	for line in inputLines:
		sum += len(line)
		lineOffsets.append(sum)

	tokensNoWs = list(generate_tokens(io.StringIO(srcString).readline))

	tokens = []

	# collect info about corresponding opening and closing brackets
	# as well as indents and dedents
	bracketStack = []
	indentStack = []

	lastTokenEndLC = (0, 0)
	for t_ in tokensNoWs:
		l, c = lastTokenEndLC
		lastTokenEnd = lineOffsets[l]+c
		l, c = t_.start
		tokenStart = lineOffsets[l]+c

		whiteSpace = srcString[lastTokenEnd:tokenStart]
		for i, ws in enumerate(whiteSpace.split("\\\n")):
			if i>0:
				tokens.append(Token(ESCAPED_NL, "\\\n"))
			tokens.append(Token(WHITESPACE, ws))

		if t_.type == OP and t_.string in "([{":
			t = ScopeToken(t_.type, t_.string, t_.start[0])
			if len(bracketStack) > 0:
				t.outer = bracketStack[-1]
			bracketStack.append(t)
		elif t_.type == OP and t_.string in "}])":
			t = ScopeToken(t_.type, t_.string, t_.start[0])
			if len(bracketStack) > 0:
				t.corresponding = bracketStack.pop()
				t.corresponding.corresponding = t
		elif t_.type == INDENT:
			t = ScopeToken(t_.type, t_.string, t_.start[0])
			if len(indentStack) > 0:
				t.outer = indentStack[-1]
			indentStack.append(t)
		elif t_.type == DEDENT:
			t = ScopeToken(t_.type, t_.string, t_.start[0])
			if len(indentStack) > 0:
				t.corresponding = indentStack.pop()
				t.corresponding.corresponding = t
		else:
			t = Token(t_.type, t_.string, t_.start[0])

		tokens.append(t)

		lastTokenEndLC = t_._asdict()["end"] # validate fails on .end

	# remove very first white space
	tokens = tokens[1:]		

	# main formatting pass, also group tokens into lines
	currentLine = Line(breakBefore=None)
	lines = [currentLine]
	logicalIndent = 0
	opticalIndent = 0
	addOpticalIndentNextLine = 0
	bracketLevel = 0

	for i, t in enumerate(tokens):
		currentLine.tokens.append(t)
		t.line = currentLine

		if t.type in [NEWLINE, NL, ESCAPED_NL]:
			currentLine.logicalIndent = logicalIndent
			currentLine.opticalIndent = opticalIndent
			# new line
			currentLine = Line(t.type)
			lines.append(currentLine)
			opticalIndent += addOpticalIndentNextLine
			addOpticalIndentNextLine = 0
			if t.type == ESCAPED_NL and bracketLevel == 0:
				opticalIndent += 1
				addOpticalIndentNextLine -= 1

		elif t.type == OP and t.srcString in "([{":
			bracketLevel += 1
			if(
				t.outer is not None
				and t.corresponding is not None
				and t.outer.corresponding is not None
				and t.outer.line == t.line
				and t.corresponding.line == t.outer.corresponding.line
			):
				t.coalesce = True
				t.corresponding.coalesce = True
			else:
				addOpticalIndentNextLine += 1

		elif t.type == OP and t.srcString in "}])":
			if bracketLevel > 0:
				bracketLevel -= 1
			if not t.coalesce:
				if len(currentLine.tokens) == 2:
					# this is the first token after the whitespace, dedent this line already
					opticalIndent -= 1
				else:
					# keep this line indented
					addOpticalIndentNextLine -= 1

		elif t.type == INDENT:
			t.newString = ""
			logicalIndent += 1
			opticalIndent += 1
			# find token that indented this block (if, def, etc; first NAME after last but one NEWLINE)
			# also find the colon and indent all lines between the colon and the INDENT
			j = i
			newLines = 0
			colon = None
			while j > 0 and newLines < 2:
				newLines += tokens[j].type == NEWLINE
				if colon is None and tokens[j].srcString == ":":
					colon = tokens[j]
				j -= 1
			while j < i and tokens[j].type != NAME:
				j += 1
			t.blockHead = tokens[j] if tokens[j].type == NAME else None
			if colon is not None:
				ln = lines.index(colon.line) + 1
				while ln < len(lines) - 1:
					lines[ln].logicalIndent += 1
					lines[ln].opticalIndent += 1
					ln += 1

		elif t.type == DEDENT:
			logicalIndent -= 1
			opticalIndent -= 1

			if insertEnd:
				if len(tokens) > i + 2:
					nextToken = tokens[i+2] # i+1 is Whitespace

				if nextToken.srcString in ["elif", "else", "catch", "finally", blockEndMarker] \
						or t.corresponding.blockHead.srcString == "case":
					pass
				else:
					# move the end marker up so empty lines don't belong to the block
					originalIndentBeforeDedent = len(t.corresponding.blockHead.line.tokens[0].srcString)

					ln = len(lines) - 2

					while ln > 0:
						if (
							# empty line, only WHITESPACE and \n
							len(lines[ln].tokens) == 2
							or (
								# we also move past comments if they were originally
								# not indented further than the current line
								lines[ln].tokens[1].type == COMMENT
								and len(lines[ln].tokens[0].srcString) <= originalIndentBeforeDedent
							)
						):
							lines[ln].logicalIndent -= 1
							lines[ln].opticalIndent -= 1
							ln -= 1
						else:
							ln += 1
							break

					endLine = Line(lines[ln].breakBefore)
					lines[ln].breakBefore = NEWLINE
					lines.insert(ln, endLine)
					endLine.tokens.append(Token(WHITESPACE, "\t" * logicalIndent, -1))
					endLine.tokens.append(Token(NAME, blockEndMarker, -1))
					endLine.tokens.append(Token(NEWLINE, "\n", -1))

		elif t.type == WHITESPACE:
			prv = tokens[i-1]
			nxt = tokens[i+1]

			noSpaceAround = [INDENT, DEDENT, NEWLINE, NL, ENCODING, ENDMARKER]
			skip = [WHITESPACE, NL, ESCAPED_NL, COMMENT, INDENT, DEDENT]

			def isExpressionEnd(token):
				return token.srcString in ["True", "False", "None", ")", "]", "}", "..."] \
					or token.type in [NAME, NUMBER, STRING]
			
			if ( # don't insert spaces after:
				len(prv.srcString) > 0 and prv.srcString[-1] in ["(", "[", "{", ".", "~", "\t", "\n"]
				or prv.srcString == "**"
				or prv.type in noSpaceAround
			):
				t.newString = ""
			elif ( # don't insert spaces before:
				len(nxt.srcString) > 0 and nxt.srcString[0] in [")", "]", "}", ".", ",", ":", ";", "\t", "\n"]
				or nxt.type in noSpaceAround
			):
				t.newString = ""
			elif ( # don't insert spaces before call or subscript brackets
				(prv.type == NAME or prv.type == NUMBER or prv.type == STRING or prv.srcString in [")", "]", "..."])
				and prv.srcString not in keyword.kwlist
				and nxt.srcString in ["(", "["]
			):
				t.newString = ""
			elif prv.type == OP and prv.srcString in ["+", "-", "*"]:
				j = i-2
				while j>0 and tokens[j].type in skip: j-=1
				if isExpressionEnd(tokens[j]):
					t.newString = " " # infix +/-
				else:
					t.newString = "" # prefix +/-
			else:
				t.newString = " "

			if nxt.srcString == "**": # "a**b" or ", **kwargs)"
				j = i-1
				while j>0 and tokens[j].type in skip: j-=1
				if isExpressionEnd(tokens[j]):
					t.newString = "" # infix +/-



	# remove the last (always empty) line
	del lines[-1]


	# find "Continuation line with same indent as next logical line" and solve with further indentation
	for i, line in enumerate(lines):
		if i==0: continue
		if line.opticalIndent == lines[i-1].opticalIndent \
				and line.logicalIndent != lines[i-1].logicalIndent:
			j = i - 1
			while j>1 and lines[j-1].opticalIndent >= line.opticalIndent:
				j -= 1
			for k in range(j, i):
				lines[k].opticalIndent += 1

	ostream = []
	for line in lines:
		if len(line.tokens) > 2: # empty lines have 2 tokens: WHITESPACE and \n
			if debug:
				ostream.append("⊢−−⊣" * line.opticalIndent)
			else:
				ostream.append("\t" * line.opticalIndent)
		for t in line.tokens:
			if t.type == INDENT and debug:
				ostream.append(">")
			elif t.type == DEDENT and debug:
				ostream.append("<")
			else:
				if debug:
					ostream.append(t.newString.replace(" ", "⎵").replace("\n", "↲\n"))
				else:
					ostream.append(t.newString)

	result = "".join(ostream)

	if validate and not debug:
		formattedTokens = list(generate_tokens(io.StringIO(result).readline))

		# if we remove all end+NEWLINE, comments and NLs, do we get the same token sequence as before formatting?
		def filterForComparison(tokenStream):
			filtered = []
			i = 0
			while i+1 < len(tokensNoWs):
				if tokensNoWs[i].string == blockEndMarker and tokensNoWs[i+1].type == NEWLINE:
					i += 2
					continue
				elif tokensNoWs[i].type not in [NL, COMMENT]:
					filtered.append(tokensNoWs[i])
				i += 1
			return filtered
			
		filteredOriginalTokens = filterForComparison(tokensNoWs)
		filteredFormattedTokens = filterForComparison(formattedTokens)

		for t1, t2 in zip(filteredOriginalTokens, filteredFormattedTokens):
			assert t1.type == t2.type
			if t1.type != INDENT:
				assert t1.string == t2.string
		assert len(filteredOriginalTokens) == len(filteredFormattedTokens)

		# is there a DEDENT before every end?
		endDefined = False
		for i, t in enumerate(formattedTokens):
			if t.string == blockEndMarker:
				if not endDefined:
					endDefined = True
				else:
					assert formattedTokens[i-1].type == DEDENT

		# is there a "elif", "else", "catch", "finally" or blockEndMarker after every DEDENT?
		for i, t in enumerate(formattedTokens):
			if t.type == DEDENT:
				assert formattedTokens[i+1].string in ["elif", "else", "catch", "finally", blockEndMarker]

	return result


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
		outFile.write(fmt(src, debug = args.debug))
