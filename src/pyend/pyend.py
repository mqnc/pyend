#! /usr/bin/env python3

from tokenize import generate_tokens, detect_encoding, \
	NAME, NUMBER, STRING, OP, INDENT, DEDENT, NEWLINE, NL, COMMENT, ENCODING, ENDMARKER
import io
import keyword

blockEndMark = "end" # has to be a single token to work
# (will otherwise not be categorized as implicit block-end-mark when formatting already formatted code)

end = None

def fmt(
	src,
	insertEnd,
	ignoreIndent,
	stripEnd,
	defineEnd,
	isClipboard,
	indentWith = "\t",
	validate = True,
	debug = False
):

	implicitBlockEnd = ["elif", "else", "catch", "finally"]


	# helpers
	class Line:
		__slots__ = ("breakBefore", "tokens", "logicalIndent", "opticalIndent")
		def __init__(self, breakBefore):
			self.breakBefore = breakBefore
			self.tokens = []
			self.logicalIndent = 0
			self.opticalIndent = 0
		end
		def __repr__(self):
			return repr(self.tokens)
		end
	end

	class Token:
		__slots__ = ("type", "srcString", "newString", "originalLine", "line")
		def __init__(self, type, srcString, origLine = None):
			self.type = type
			self.srcString = srcString
			self.newString = srcString
			self.originalLine = origLine
			self.line = None
		end
		def __repr__(self):
			return self.srcString
		end
	end

	class ScopeToken(Token):
		__slots__ = ("corresponding", "outer", "blockHead", "coalesce")
		def __init__(self, *args, **kwargs):
			super(ScopeToken, self).__init__(*args, **kwargs)
			self.corresponding = None # corresponding opening/closing token
			self.outer = None # for opening tokens, the opening token one level higher
			self.coalesce = False # for brackets, whether they don't need extra indentation
			self.blockHead = None # for indents the token at the start of the block
		end
	end

	WHITESPACE = -1
	ESCAPED_NL = -2
	BLOCK_START = -3
	BLOCK_END = -4



	# convert to string
	if type(src) == bytes:
		encoding = detect_encoding(io.BytesIO(src).readline)[0]
		srcString = src.decode(encoding)
	else:
		srcString = src
	end

	# always end with \n
	if srcString[-1] != "\n":
		srcString += "\n"
	end

	# tokenize
	inputLines = []
	tokensNoWs = []

	if ignoreIndent:
		# We need to strip all indentation before tokenizing because the tokenizer can throw
		# if the source is badly indented. However, we cannot simply remove leading space
		# from all source lines because we must not change multi line strings. So there is
		# this line by line dance with the tokenizer going on now:
		strip = True
		buf = io.StringIO(srcString)

		def readLineAndStripExceptInStrings():
			nonlocal strip, inputLines
			line = buf.readline()
			if strip:
				strip = False
				line = line.lstrip(" \t")
			end
			inputLines.append(line)
			return line
		end

		for t in generate_tokens(readLineAndStripExceptInStrings):
			tokensNoWs.append(t)
			strip = True
		end

		srcString = "".join(inputLines)
	else:
		inputLines = io.StringIO(srcString).readlines()
		tokensNoWs = list(generate_tokens(io.StringIO(srcString).readline))
	end

	inputLines.append("")

	# for converting (line, column) to char index
	lineOffsets = [0, 0]
	sum = 0
	for line in inputLines:
		sum += len(line)
		lineOffsets.append(sum)
	end

	tokens = []

	# collect info about corresponding opening and closing brackets
	# as well as indents and dedents
	# also detect if end is defined
	bracketStack = []
	indentStack = []

	lastTokenEndLC = (0, 0)
	for i, t_ in enumerate(tokensNoWs):
		l, c = lastTokenEndLC
		lastTokenEnd = lineOffsets[l] + c
		l, c = t_.start
		tokenStart = lineOffsets[l] + c

		whiteSpace = srcString[lastTokenEnd: tokenStart]
		for j, ws in enumerate(whiteSpace.split("\\\n")):
			if j > 0:
				tokens.append(Token(ESCAPED_NL, "\\\n"))
			end
			tokens.append(Token(WHITESPACE, ws))
		end

		if t_.string in ["(", "[", "{"]:
			t = ScopeToken(t_.type, t_.string, t_.start[0])
			if len(bracketStack) > 0:
				t.outer = bracketStack[-1]
			end
			bracketStack.append(t)
		elif t_.string in ["}", "]", ")"]:
			t = ScopeToken(t_.type, t_.string, t_.start[0])
			if len(bracketStack) > 0:
				t.corresponding = bracketStack.pop()
				t.corresponding.corresponding = t
			end
		elif t_.type == INDENT:
			t = ScopeToken(t_.type, t_.string, t_.start[0])
			if len(indentStack) > 0:
				t.outer = indentStack[-1]
			end
			indentStack.append(t)
		elif t_.type == DEDENT:
			t = ScopeToken(t_.type, t_.string, t_.start[0])
			if len(indentStack) > 0:
				t.corresponding = indentStack.pop()
				t.corresponding.corresponding = t
			end
		elif (
			t_.string == ":"
			and tokensNoWs[i + 1].type in [NEWLINE, COMMENT]
		):
			t = Token(BLOCK_START, t_.string, t_.start[0])
		elif (
			t_.string == blockEndMark
			and tokensNoWs[i - 1].type in [NEWLINE, NL, DEDENT, INDENT]
			and tokensNoWs[i + 1].type in [NEWLINE, COMMENT]
		):
			t = Token(BLOCK_END, t_.string, t_.start[0])
		else:
			t = Token(t_.type, t_.string, t_.start[0])
		end

		tokens.append(t)

		lastTokenEndLC = t_.end
	end

	# remove very first white space
	tokens = tokens[1:]

	# if we work on the clipboard and start indented, remove the dedent in the end (and the whitespace)
	if isClipboard and tokens[0].type == INDENT and tokens[-3].type == DEDENT:
		del tokens[-3]
		del tokens[-2]
	end

	# main formatting pass, also group tokens into lines
	currentLine = Line(breakBefore = None)
	lines = [currentLine]
	logicalIndent = 0
	opticalIndent = 0
	addLogicalIndentNextLine = 0
	addOpticalIndentNextLine = 0
	bracketStack = []
	endDefinedBeforeFirstOccurance = None

	for i, t in enumerate(tokens):
		currentLine.tokens.append(t)
		t.line = currentLine

		if t.type in [NEWLINE, NL, ESCAPED_NL]:
			currentLine.logicalIndent = logicalIndent
			currentLine.opticalIndent = opticalIndent
			# new line
			currentLine = Line(t.type)
			lines.append(currentLine)
			logicalIndent += addLogicalIndentNextLine
			opticalIndent += addOpticalIndentNextLine
			addLogicalIndentNextLine = 0
			addOpticalIndentNextLine = 0
			if t.type == ESCAPED_NL and len(bracketStack) == 0:
				opticalIndent += 1
				addOpticalIndentNextLine -= 1
			end

		elif t.srcString in ["(", "[", "{"]:
			bracketStack.append(t.srcString)
			if (
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
			end

		elif t.srcString in ["}", "]", ")"]:
			if len(bracketStack) > 0:
				bracketStack.pop()
			end
			if not t.coalesce:
				if len(currentLine.tokens) == 2:
					# this is the first token after the whitespace, dedent this line already
					opticalIndent -= 1
				else:
					# keep this line indented
					addOpticalIndentNextLine -= 1
				end
			end

		elif ignoreIndent and t.type == BLOCK_START:
			addLogicalIndentNextLine += 1
			addOpticalIndentNextLine += 1

		elif ignoreIndent and t.type == BLOCK_END:
			logicalIndent -= 1
			opticalIndent -= 1
			if endDefinedBeforeFirstOccurance is None:
				endDefinedBeforeFirstOccurance = False
			end

		elif (
			t.srcString == blockEndMark
			and endDefinedBeforeFirstOccurance is None
			and logicalIndent == 0
			and len(tokens) > i + 2
			and tokens[i + 2].srcString == "="
		):
			j = i - 1
			while j > 0 and tokens[j].type in [WHITESPACE, NL, ESCAPED_NL, COMMENT]:
				j -= 1
			end
			if tokens[j].type == NEWLINE:
				endDefinedBeforeFirstOccurance = True
			end

		elif (
			t.srcString == blockEndMark
			and endDefinedBeforeFirstOccurance is None
			and logicalIndent == 0
			and i > 2
			and tokens[i - 2].srcString == "import"
		):
			endDefinedBeforeFirstOccurance = True

		elif ignoreIndent and t.srcString in implicitBlockEnd:
			# we could be fooled by a deceptively constructed ternary if, so check if there was a NEWLINE before
			j = i - 1

			while j > 0 and tokens[j].type in [WHITESPACE, NL, ESCAPED_NL, COMMENT]:
				j -= 1
			end
			if tokens[j].type == NEWLINE:
				logicalIndent -= 1
				opticalIndent -= 1
			end

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
				end
				j -= 1
			end
			while j < i and tokens[j].type != NAME:
				j += 1
			end
			t.blockHead = tokens[j] if tokens[j].type == NAME else None
			if colon is not None:
				ln = lines.index(colon.line) + 1
				while ln < len(lines) - 1:
					lines[ln].logicalIndent += 1
					lines[ln].opticalIndent += 1
					ln += 1
				end
			end

		elif t.type == DEDENT:
			logicalIndent -= 1
			opticalIndent -= 1

			if endDefinedBeforeFirstOccurance is None:
				endDefinedBeforeFirstOccurance = False
			end

			if len(tokens) > i + 2:
				nextToken = tokens[i + 2] # i+1 is Whitespace
			end

			if (
				nextToken.type == BLOCK_END
				or nextToken.srcString in implicitBlockEnd
				or t.corresponding.blockHead is not None and t.corresponding.blockHead.srcString == "case"
			):
				pass
			else:
				# move the end mark up so empty lines don't belong to the block
				if t.corresponding.blockHead is not None:
					headLine = t.corresponding.blockHead.line
					originalIndentBeforeDedent = len(headLine.tokens[0].srcString) # whitespace
					if headLine.tokens[1].type == INDENT:
						originalIndentBeforeDedent += len(headLine.tokens[1].srcString)
					end
				else:
					originalIndentBeforeDedent = 0
				end

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
						# possibly correct comment indentation
						lines[ln].logicalIndent -= 1
						lines[ln].opticalIndent -= 1
						ln -= 1
					else:
						ln += 1
						break
					end
				end

				if insertEnd:
					endLine = Line(lines[ln].breakBefore)
					lines[ln].breakBefore = NEWLINE
					lines.insert(ln, endLine)
					endLine.tokens.append(Token(WHITESPACE, "", -1))
					endLine.tokens.append(Token(BLOCK_END, blockEndMark, -1))
					endLine.tokens.append(Token(NEWLINE, "\n", -1))
					endLine.logicalIndent = logicalIndent
					endLine.opticalIndent = logicalIndent
				end
			end

		elif t.type == WHITESPACE:
			prv = tokens[i - 1]
			nxt = tokens[i + 1]

			noSpaceAround = [INDENT, DEDENT, NEWLINE, NL, ENCODING, ENDMARKER]
			skip = [WHITESPACE, NL, ESCAPED_NL, COMMENT, INDENT, DEDENT]

			def isExpressionEnd(token):
				return token.srcString in ["True", "False", "None", ")", "]", "}", "..."] \
					or token.type in [NAME, NUMBER, STRING]
			end

			if ( # space before comment overrules many of the following rules
				nxt.type == COMMENT
				and not (
					len(prv.srcString) > 0
					and prv.srcString[-1] in ["\t", "\n"]
				)
				and not prv.srcString in noSpaceAround
			):
				t.newString = " "
			elif ( # don't insert spaces after:
				len(prv.srcString) > 0 and prv.srcString[-1] in ["(", "[", "{", ".", "~", "\t", "\n"]
				or prv.srcString == "**"
				or prv.type in noSpaceAround
			):
				t.newString = ""
			elif ( # don't insert spaces after ":" inside []
				nxt.srcString == ":"
				and len(bracketStack) > 0
				and bracketStack[-1] == "["
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
				j = i - 2
				while j > 0 and tokens[j].type in skip: j -= 1
				if isExpressionEnd(tokens[j]):
					t.newString = " " # infix +/-
				else:
					t.newString = "" # prefix +/-
				end
			else:
				t.newString = " "
			end

			if nxt.srcString == "**": # "a**b" or ", **kwargs)"
				j = i - 1
				while j > 0 and tokens[j].type in skip: j -= 1
				if isExpressionEnd(tokens[j]):
					t.newString = "" # infix +/-
				end
			end
		end
	end

	# remove the last (always empty) line after the mandatory last linebreak
	del lines[-1]


	# find "Continuation line with same indent as next logical line" and solve with further indentation
	for i, line in enumerate(lines):
		if i == 0: continue
		if line.opticalIndent == lines[i - 1].opticalIndent \
				and line.logicalIndent != lines[i - 1].logicalIndent:
			j = i - 1
			while j > 1 and lines[j - 1].opticalIndent >= line.opticalIndent:
				j -= 1
			end
			for k in range(j, i):
				lines[k].opticalIndent += 1
			end
		end
	end

	# strip end marks (only flag them and exclude them in the next step as removing items from lists is expensive)
	dontOutput = set()
	if stripEnd:
		for line in lines:
			for i, t in enumerate(line.tokens):
				if t.type == BLOCK_END:
					if len(line.tokens) > i + 2 and line.tokens[i + 2].type == COMMENT:
						dontOutput.add(id(t))
						dontOutput.add(id(line.tokens[i + 1]))
					else:
						dontOutput.add(id(line))
					end
				end
			end
		end
	end

	# compose output
	ostream = []

	if not isClipboard and endDefinedBeforeFirstOccurance != True and insertEnd:
		shebang = lines[0].tokens[0]
		if (
			shebang.type == COMMENT
			and len(shebang.srcString) >= 2
			and shebang.srcString[0: 2] == "#!"
		):
			ostream.append(shebang.newString + "\n" + defineEnd + "\n")
			dontOutput.add(id(lines[0]))
		else:
			ostream.append(defineEnd + "\n")
		end
	end

	for line in lines:
		if id(line) in dontOutput:
			continue
		end
		if len(line.tokens) > 2: # empty lines have 2 tokens: WHITESPACE and \n
			if debug:
				ostream.append("⊢−−⊣" * line.opticalIndent)
			else:
				ostream.append(indentWith * line.opticalIndent)
			end
		end
		for t in line.tokens:
			if id(t) in dontOutput:
				continue
			elif t.type == INDENT and debug:
				ostream.append(">")
			elif t.type == DEDENT and debug:
				ostream.append("<")
			else:
				if debug:
					ostream.append(t.newString.replace(" ", "⎵").replace("\n", "↲\n"))
				else:
					ostream.append(t.newString)
				end
			end
		end
	end

	result = "".join(ostream)

	if validate and not debug:
		formattedTokens = list(generate_tokens(io.StringIO(result).readline))

		# if we remove all end+NEWLINE, comments and NLs, do we get the same token sequence as before formatting?
		def filterForComparison(tokenStream):
			filtered = []
			i = 0
			while i + 1 < len(tokensNoWs):
				if tokensNoWs[i].string == blockEndMark and tokensNoWs[i + 1].type == NEWLINE:
					i += 2
					continue
				elif tokensNoWs[i].type not in [NL, COMMENT]:
					filtered.append(tokensNoWs[i])
				end
				i += 1
			end
			return filtered
		end

		filteredOriginalTokens = filterForComparison(tokensNoWs)
		filteredFormattedTokens = filterForComparison(formattedTokens)

		for t1, t2 in zip(filteredOriginalTokens, filteredFormattedTokens):
			assert t1.type == t2.type
			if t1.type != INDENT:
				assert t1.string == t2.string
			end
		end
		assert len(filteredOriginalTokens) == len(filteredFormattedTokens)

		# is there a DEDENT before every alone-on-its-line end?
		for i, t in enumerate(formattedTokens):
			if (
				t.string == blockEndMark
				and formattedTokens[i - 1].type in [NEWLINE, NL, DEDENT, INDENT]
				and formattedTokens[i + 1].type in [NEWLINE, COMMENT]
			):
				assert formattedTokens[i - 1].type == DEDENT
			end
		end

		# is there a "elif", "else", "catch", "finally" or blockEndMark after every DEDENT?
		if insertEnd:
			for i, t in enumerate(formattedTokens):
				if t.type == DEDENT:
					assert formattedTokens[i + 1].string in ["elif", "else", "catch", "finally", blockEndMark] \
						or isClipboard and formattedTokens[i + 1].type == ENDMARKER
				end
			end
		end
	end

	return result
end

def main_cli():
	import argparse
	import pyperclip

	parser = argparse.ArgumentParser(prog = "pyend",
		description = "format python files and insert block end marks")

	parser.add_argument("filename", nargs = '?', help = "input file name")
	parser.add_argument("-o", "--out", help = "output file name, input file is overwritten if omitted")
	parser.add_argument("-c", "--clipboard", action = "store_true", help = "use clipboard content as input (and output if no output file is specified)")
	parser.add_argument("-e", "--insert-end", action = "store_true", help = "insert end marks based on indentation")
	parser.add_argument("-i", "--ignore-indent", action = "store_true", help = "ignore indentation and format code only based on end marks")
	parser.add_argument("-s", "--strip-end", action = "store_true", help = "remove all end marks")
	parser.add_argument("-n", "--end-is-none", action = "store_true", help = "use 'end = None' instead of 'from pyend import end'")
	parser.add_argument(
		"--convert-tabs-to-spaces-despite-tabs-being-objectively-better-than-spaces", action = "store_true")
	parser.add_argument(
		"--use-this-many-spaces-per-tab-cuz-as-a-spacist-i-want-uniformity-but-i-dont-want-the-default",
		type = int, default = 11, metavar = "NUMBER", help = "(default is 11)"
	)
	parser.add_argument("--april", action = "store_true", help = "acknowledge that this is an April Fool's joke and that you're not actually going to migrate your codebase")

	args = parser.parse_args()

	if not args.april:
		print("""
APRIL FOOLS! HAHA! Should have seen your face.

There won't be a Python4 anytime soon. However, you can still actually use pyend
to insert block end markers in your code and format based on that. Just start it
with the --april flag in order to acknowledge that this is an April Fool's joke
and that you're not actually going to migrate your codebase.
""")
		parser.print_usage()
		return 2
	end

	if args.filename is None and not args.clipboard \
			or args.filename is not None and args.clipboard:
		parser.print_usage()
		print("error: specify either an input file or --clipboard")
		return 2
	end

	if args.insert_end and args.ignore_indent:
		parser.print_usage()
		print("error: can only insert end marks (-e) if the code is properly indented")
		print("or ignore indentation (-i) if all blocks have end marks")
		return 2
	end

	if args.insert_end and args.strip_end:
		parser.print_usage()
		print("error: can either insert end marks (-e) or strip end marks (-s)")
		return 2
	end

	if args.filename is not None:
		with open(args.filename) as inFile:
			src = inFile.read()
		end
	elif args.clipboard:
		src = pyperclip.paste()
	end

	formatted = fmt(
		src,
		insertEnd = args.insert_end,
		ignoreIndent = args.ignore_indent,
		stripEnd = args.strip_end,
		defineEnd = (
			f"{blockEndMark} = None" if args.end_is_none
			else f"from pyend import {blockEndMark}" # viral marketing
		),
		isClipboard = args.clipboard,
		indentWith = (
			"\t" if not args.convert_tabs_to_spaces_despite_tabs_being_objectively_better_than_spaces
			else " " * args.use_this_many_spaces_per_tab_cuz_as_a_spacist_i_want_uniformity_but_i_dont_want_the_default
		),
		debug = False
	)

	out = None
	if args.out is not None:
		out = args.out
	elif args.clipboard:
		pyperclip.copy(formatted)
	else:
		out = args.filename
	end

	if out is not None:
		with open(out, "w") as outFile:
			outFile.write(formatted)
		end
	end

	return 0
end

if __name__ == "__main__":
	import sys
	sys.exit(main_cli())
end
