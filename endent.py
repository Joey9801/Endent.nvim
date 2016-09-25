import re

import neovim

@neovim.plugin
class EndentPlugin(object):

    def __init__(self, nvim):
        self.nvim = nvim

    @neovim.command("EndentVariables", range='', nargs='*')
    def endent_variables(self, args, range):
        lines_slice = slice(range[0]-1, range[1])

        lines = self.nvim.current.buffer[lines_slice]
        formatted_lines = align_variables(lines)
        self.nvim.current.buffer[lines_slice] = formatted_lines


def split_variable_declaration(line):
    """
    Splits a variable declaration into 6 components. Correctly formatted list
    of variable declarations can be made by concatentating these components
    with varying numbers of spaces, such that they line up correctly.

    The components are as follows:
        type, asterisks, name, equals, assignment, semicolon

    If these fields are not present in the input, they are an empty string in
    the output.
    Leading whitespace is thrown away.
    """

    if len(line) == 0:
        return None

    #Ghastly regex ensures things inside quoutes are left alone
    token_regex = ("(?x)       "
                   "([ *=;]*)  "   #Split on 0 or more of these characters
                   "(?=        "   #Followed by:
                   "  (?:      "   #Start of non-capture group
                   "    [^\"]* "   #0 or more non-quoute characters
                   "    \"     "   #1 quoute
                   "    [^\"]* "   #0 or more non-quoute characters
                   "    \"     "   #1 quoute
                   "  )*       "   #0 or more repetitions of non-capture group
                   "  [^\"]*   "   #0 or more non-quoutes
                   "  $        "   #Until the end
                   ")          ")


    #Get the non-whitespace tokens in a list
    tokens = re.split(token_regex, line)
    tokens = [x for x in tokens if len(x) > 0 and not x.isspace()]

    #Remove whitespace from the asterisk and space tokens
    for i, tok in enumerate(tokens):
        if "*" in tok or "=" in tok:
            tokens[i] = tok.replace(" ", "")

    components = [""]*6

    first_split = 0
    if "=" in tokens:
        first_split = tokens.index("=")
    elif ";" in tokens:
        first_split = tokens.index(";")
    else:
        return None

    #The last token before the first_split is the name
    components[2] = tokens[first_split-1]

    #If the token before the name is only asterisks, it is the asterisk
    #component
    #Join everything before this to get the type component
    if tokens[first_split-2] == (len(tokens[first_split-2]) * "*"):
        components[1] = tokens[first_split-2]
        components[0] = " ".join(tokens[0:first_split-2])
    else:
        components[0] = " ".join(tokens[0:first_split-1])


    if tokens[first_split] == "=":
        components[3] = "="
        if ";" in tokens:
            components[4] = " ".join(tokens[first_split+1:tokens.index(";")])
        else:
            components[4] = " ".join(tokens[first_split+1:-1])


    if ";" in tokens:
        components[5] = ";"

    return components



def align_variables(lines):
    """
    Returns a list of lines semantically identical to the input lines, but
    properly aligned.
    """

    #First non-space character -> the indentation level
    indentation = re.search('[^ ]', lines[0]).start()

    split_lines = [split_variable_declaration(line) for line in lines]
    split_lines = [sline for sline in split_lines if sline != None]


    #Find the first alignment point -> the number of characters which should
    #appear before the variable name.
    first_align  = 0
    for sline in split_lines:
        first_align = max(first_align, len(sline[0]) + len(sline[1]) + 1)

    #Find the second alignment point, the number of characters which should
    #appear before an equals sign
    second_align = 0
    for sline in split_lines:
        if sline[3] == "=":
            second_align = max(second_align,
                               first_align + len(sline[2]) + 1)

        print(sline, first_align, second_align)

    lines = [""]*len(lines)
    for i, sline in enumerate(split_lines):
        first_spaces = first_align - len(sline[0]) - len(sline[1])

        lines[i] = ( " "*indentation  +
                     sline[0]         +
                     " "*first_spaces +
                     sline[1] + sline[2])

        if sline[3] == "=":
            second_spaces = second_align - (len(lines[i]) - indentation)
            lines[i] += ( " "*second_spaces +
                          "= "              +
                          sline[4])

        lines[i] += sline[5]

    return lines


if __name__ == "__main__":
    
    with open("test_cases.txt") as f:
        lines = [x for x in f.readlines() if len(x) > 0]

    for aligned in align_variables(lines):
        print(aligned)

