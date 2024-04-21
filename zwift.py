# This program transforms a simple textual bike workout description into
# a Zwift workout.
#
# The input must conform to the following grammar (specified in EBNF):
#  Workout = Stages FTP
#  FTP = "|" Integer WUnit
#  Integer = Digit { Digit }
#  Digit = "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"
#  Stages = Stage { "+" Stage }
#  Stage = Integer "*" "(" Stages ")") | Time "@" Effort
#  Time = (Integer | Float) TUnit
#  Float = Integer "." Integer
#  TUnit = "m" | "M" | "s" | "S" | "h" | "H"
#  Effort = Watts ("/" Cadence "-" Cadence)?
#  Watts = Integer WUnit [ "-" Integer WUnit ] | "_"
#  WUnit = ("w" | "W")
#  Cadence = Integer CUnit
#  CUnit = ("c" | "C")

# MIT License
#
# Copyright (c) 2023-2024 Rainer Koschke
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import string
import sys
import getopt
import typing
from enum import Enum
from typing import List
from datetime import timedelta
from os.path import exists

VERSION: str = "1.1"
"""
The version of this script.
"""


class TokenType(str, Enum):
    """
    A token type and how it should be printed.
    """
    Plus = "+"
    Minus = "-"
    Multiply = "*",
    OpeningBracket = "(",
    ClosingBracket = ")",
    Pipe = "|",
    At = "@",
    Slash = "/",
    Float = "Float",
    Integer = "Integer",
    Watt = "w",
    Cadence = "c",
    Hour = "h",
    Minute = "m",
    Second = "s",
    DontCare = "_",
    End = "<EndOfInput>"


class Token:
    """
    A token created by the lexical analysis.
    """
    type: TokenType = TokenType.End
    """
        The type of this token.
    """
    value: float = 0
    """
        The value of this token in case it is a number.
        This value is defined only for the token types Integer and Float.
    """

    def __init__(self, t: TokenType, value: float = 0):
        """
        Constructor setting the type and value of this token.
        :param t: the token type to be assigned
        :param value: the value of the token in case of Integer and Float tokens
        """
        self.type = t
        self.value = value


class Treatment:
    """
    A treatment of a workout.
    This is the super class of concrete treatments such as a duration
    a Zwift user is to hold a certain power.
    """
    seconds: float = 0.0
    """
    The duration of the treatment in seconds.
    """
    lower_cadence: int = 0
    """
    The lower value of the target cadence range. Cannot be less than 0.
    """
    upper_cadence: int = 0
    """
    The upper value of the target cadence range. Cannot be less than 0.
    Cannot be less than lower_cadence.
    If lower_cadence and upper_cadence are both 0, a cadence range will
    not be emitted.
    """

    def __str__(self) -> str:
        """
        Yields a human-readable representation of this treatment.
        :return: a human-readable representation of this treatment
        """
        return "ABSTRACT_TREATMENT()"

    def to_zwift(self, file: typing.TextIO, ftp: float) -> None:
        """
        Adds a textual representation of this treatment according to a Zwift workout file.
        :param file: where to emit the representation
        :param ftp: the user's FTP value
        :return: None
        """
        print("", file=file)

    def cadence_to_zwift(self) -> str:
        """
        :return:
        """
        if self.lower_cadence == 0 and self.upper_cadence == 0:
            return ""
        else:
            return f" CadenceLow=\"{str(self.lower_cadence)}\" CadenceHigh=\"{str(self.upper_cadence)}\""


class Free(Treatment):
    """
    A free ride, that is, one in which there is no prescribed target power.
    """

    def __str__(self) -> str:
        """
        Yields a human-readable representation of this treatment.
        :return: a human-readable representation of this treatment
        """
        return f"free({str(self.seconds)}s {str(self.lower_cadence)}c-{str(self.upper_cadence)}c)"

    def to_zwift(self, file: typing.TextIO, ftp: float) -> None:
        """
        Adds a FreeRide clause.
        :param file: where to emit the representation
        :param ftp: the user's FTP value
        :return: None
        """
        print(f"     <Freeride Duration=\"{self.seconds}\"{self.cadence_to_zwift()}/>", file=file)


class Power(Treatment):
    """
    A power treatment where a user needs to hold a particular wattage.
    """
    wattage: int
    """
    The watts to be held.
    """

    def __init__(self, watts: int):
        """
        Constructor setting the watts to be held.
        :param watts: the watts to be held
        """
        self.wattage = watts

    def __str__(self) -> str:
        """
        Yields a human-readable representation of this treatment.
        :return: a human-readable representation of this treatment
        """
        return f"power({str(self.seconds)}s, {str(self.wattage)}w " \
               f"{str(self.lower_cadence)}c-{str(self.upper_cadence)}c))"

    def to_zwift(self, file: typing.TextIO, ftp: float) -> None:
        """
        Adds a SteadyState clause.
        :param file: where to emit the representation
        :param ftp: the user's FTP value
        :return: None
        """
        print(f"     <SteadyState Duration=\"{self.seconds}\" Power=\"{relative(self.wattage, ftp)}\""
              + f"{self.cadence_to_zwift()} pace=\"0\"/>", file=file)


class Range(Treatment):
    """
    A power treatment where a user needs to hold a particular wattage
    that is increased or decreased within the duration of the treatment.
    """
    start_wattage: int
    """
    The watts at the beginning of this treatment.
    """
    end_wattage: int
    """
    The watts at the end of this treatment.
    """

    def __init__(self, start: int, end: int):
        """
        Constructor setting the watts at the beginning and end of the treatment.
        :param start: watts at the beginning of this treatment
        :param end: watts at the end of this treatment
        """
        self.start_wattage = start
        self.end_wattage = end

    def __str__(self):
        """
        Yields a human-readable representation of this treatment.
        :return: a human-readable representation of this treatment
        """
        return f"power({str(self.seconds)}s, {str(self.start_wattage)}w-{str(self.end_wattage)}w " \
               f"{str(self.lower_cadence)}c-{str(self.upper_cadence)}c)"

    def to_zwift(self, file: typing.TextIO, ftp: float) -> None:
        """
        Adds a Warmup or Cooldown clause.
        Warmup will be used if start_wattage <= end_wattage; otherwise
        Cooldown will be used.
        :param file: where to emit the representation
        :param ftp: the user's FTP value
        :return: None
        """
        if self.start_wattage <= self.end_wattage:
            print(f"     <Warmup Duration=\"{self.seconds}\" PowerLow=\"{relative(self.start_wattage, ftp)}\""
                  + f" PowerHigh=\"{relative(self.end_wattage, ftp)}\""
                  + f"{self.cadence_to_zwift()} pace=\"0\"/>",
                  file=file)
        else:
            print(f"     <Cooldown Duration=\"{self.seconds}\" PowerLow=\"{relative(self.end_wattage, ftp)}\""
                  + f" PowerHigh=\"{relative(self.start_wattage, ftp)}\""
                  + f"{self.cadence_to_zwift()} pace=\"0\"/>",
                  file=file)


def relative(wattage: float, ftp: float) -> float:
    """
    Returns wattage / ftp rounded to two digits.
    :param wattage: watts to be set in relation to ftp
    :param ftp: the user's FTP value
    :return: wattage / ftp rounded to two digits
    """
    return round(wattage / ftp, 2)


def expect(expected: TokenType, tokens: list[Token]) -> list[Token]:
    """
    Checks whether the type of the first token in tokens is
    equal to given token. If so, the tail of tokens will be returned.
    If not, a syntax error will be reported and the script will terminate.
    :param expected: the expected token type
    :param tokens: the current token stream
    :return: the tail of tokens
    """
    if tokens[0].type != expected:
        print("syntax error at:")
        unparse(tokens)
        error(f'{expected.value} expected')
    return tokens[1:]


def expect_one_of(expected: list[TokenType], tokens: list[Token]) -> list[Token]:
    """
    Checks whether the type of the first token in tokens is
    contained in expected. If so, the tail of tokens will be returned.
    If not, a syntax error will be reported and the script will terminate.
    :param expected: the expected token types
    :param tokens: the current token stream
    :return: the tail of tokens
    """
    if tokens[0].type not in expected:
        unparse(tokens)
        error(f'One of {[t.value for t in expected]} expected')
    return tokens[1:]


def process(file: typing.TextIO, workout: str, author: str, description: str, name: str) -> None:
    """
    Tokenizes and parses the workout specification and emits a Zwift
    workout to given file.
    :param file: the file where to emit the Zwift workout
    :param workout: a workout specification
    :param author: the author of workout; may be empty
    :param description:  a description of the workout; may be empty
    :param name: a unique name of the workout; must not be empty
    :return: None
    """
    tokens: list[Token] = tokenize(workout)
    program: list[Treatment]
    ftp: float
    tokens, program, ftp = parse(tokens)
    if tokens[0].type != TokenType.End:
        unparse(tokens)
        error("There is superfluous input.")
    duration: float = total_time(program)
    if duration == 0:
        print("Warning: The total duration of your workout is 0. Was this intended?")
    else:
        print(f'Total time of the workout is {str(timedelta(seconds=duration))} h.')
    to_zwift(file, program, ftp, author, description, name)


def total_time(program: list[Treatment]) -> float:
    """
    Returns the total duration of the workout program in seconds.
    :param program: a workout program
    :return: total duration of the workout program in seconds
    """
    total_duration: float = 0
    for t in program:
        total_duration = total_duration + t.seconds
    return total_duration


def to_zwift(file: typing.TextIO, program: list[Treatment], ftp: float, author: str, description: str,
             name: str) -> None:
    """
    Emits a Zwift workout of the given workout program to given file.
    :param file: where to emit the Zwift workout
    :param program: workout program
    :param ftp: the user's FTP value
    :param author: the author of the workout (may be empty)
    :param description: the description of the workout (may be empty)
    :param name: the unique name of the workout (must not be empty)
    :return: None
    """
    preamble(file, author, name, description)
    for treatment in program:
        treatment.to_zwift(file, ftp)
    postamble(file)


def preamble(file: typing.TextIO, author: str, name: str, description: str) -> None:
    """
    Emits the XML code as the preamble of a Zwift workout to given file.
    :param file: where to emit the Zwift workout preamble
    :param author: the author of the workout (may be empty)
    :param description: the description of the workout (may be empty)
    :param name: the unique name of the workout (must not be empty)
    :return: None
    """
    print("<workout_file>", file=file)
    print(f"  <author>{author}</author>", file=file)
    print(f"  <name>{name}</name>", file=file)
    print(f"  <description>{description}</description>", file=file)
    print("   <sportType>bike</sportType>", file=file)
    print("   <tags></tags>", file=file)
    print("   <workout>", file=file)


def postamble(file: typing.TextIO) -> None:
    """
    Emits the XML code as the postamble of a Zwift workout to given file.
    :param file: where to emit the Zwift workout preamble
    :return: None
    """
    print("   </workout>", file=file)
    print("</workout_file>", file=file)


def parse(tokens: List[Token]) -> (List[Token], List[Treatment], float):
    """
    Parses given tokens according to the rule 'Workout = Stages FTP'.
    :param tokens: token stream not yet parsed
    :return: the tail of tokens not consumed by this parse and the treatments parsed successfully
    """
    program: List[Treatment]
    tokens, program = parse_stages(tokens)
    ftp: float
    tokens, ftp = parse_ftp(tokens)
    return tokens, program, ftp


def parse_stages(tokens: List[Token]) -> (List[Token], List[Treatment]):
    """
    Parses given tokens according to the rule 'Stages = Stage { "+" Stage }'.
    :param tokens: token stream not yet parsed
    :return: the tail of tokens not consumed by this parse and the treatments parsed successfully
    """
    program: list[Treatment]
    tokens, program = parse_stage(tokens)
    while tokens[0].type == TokenType.Plus:
        stage: list[Treatment]
        tokens, stage = parse_stage(tokens[1:])
        program = program + stage
    return tokens, program


def parse_stage(tokens: List[Token]) -> (List[Token], List[Treatment]):
    """
    Parses given tokens according to the rule 'Integer "*" "(" Stages ")") | Time "@" Effort'.
    :param tokens: token stream not yet parsed
    :return: the tail of tokens not consumed by this parse and the treatments parsed successfully
    """
    if len(tokens) > 2 and tokens[0].type == TokenType.Integer and tokens[1].type == TokenType.Multiply:
        # an interval
        factor: int = int(tokens[0].value)
        program: List[Treatment]
        tokens = expect(TokenType.OpeningBracket, tokens[2:])
        tokens, program = parse_stages(tokens)
        return expect(TokenType.ClosingBracket, tokens), program * factor
    elif tokens[0].type == TokenType.Integer or tokens[0].type == TokenType.Float:
        seconds: int
        tokens, seconds = parse_time(tokens)
        tokens = expect(TokenType.At, tokens)
        treatment: Treatment
        tokens, treatment = parse_effort(tokens)
        treatment.seconds = seconds
        return tokens, [treatment]
    else:
        unparse(tokens)
        error("Number expected.")


def parse_time(tokens: list[Token]) -> (list[Token], int):
    """
    Parses given tokens according to the rule '(Integer | Float) TUnit'.
    :param tokens: token stream not yet parsed
    :return: the tail of tokens not consumed by this parse and the time in seconds parsed
    """
    if tokens[0].type == TokenType.Integer or tokens[0].type == TokenType.Float:
        value: float = tokens[0].value
        tokens = tokens[1:]
        match tokens[0].type:
            case TokenType.Hour:
                value = round(60 * 60 * value)
            case TokenType.Minute:
                value = round(60 * value)
            case TokenType.Second:
                pass
            case _:
                expect_one_of([TokenType.Hour, TokenType.Minute, TokenType.Second], tokens)
        return tokens[1:], round(value)
    else:
        unparse(tokens)
        error("Number expected.")


def parse_effort(tokens: List[Token]) -> (List[Token], Treatment):
    """
    Parses given tokens according to rule 'Watts ("/" Cadence "-" Cadence)?'
    :param tokens: token stream not yet parsed
    :return: the tail of tokens not consumed by this parse and the treatment parsed
    """
    tokens, treatment = parse_watts(tokens)
    if tokens[0].type == TokenType.Slash:
        tokens, treatment = parse_cadence_range(tokens, treatment)
    return tokens, treatment


def parse_watts(tokens: List[Token]) -> (List[Token], Treatment):
    """
    Parses given tokens according to the rule 'Integer WUnit [ "-" Integer WUnit ] | "_"'.
    :param tokens: token stream not yet parsed
    :return: the tail of tokens not consumed by this parse and the treatment parsed
    """
    if tokens[0].type == TokenType.DontCare:
        return tokens[1:], Free()
    elif tokens[0].type == TokenType.Integer:
        value: int = int(tokens[0].value)
        tokens = expect(TokenType.Watt, tokens[1:])
        if tokens[0].type == TokenType.Minus:
            tokens = tokens[1:]
            end_value: int
            if len(tokens) > 0 and tokens[0].type == TokenType.Integer:
                end_value = int(tokens[0].value)
            else:
                end_value = -1
            tokens = expect(TokenType.Integer, tokens)
            tokens = expect(TokenType.Watt, tokens)
            return tokens, Range(value, end_value)
        else:
            return tokens, Power(value)
    else:
        error("Integer expected.")


def parse_cadence_range(tokens: List[Token], treatment: Treatment) -> (List[Token], Treatment):
    """
    Parses given tokens according to the rule '"/" Cadence "-" Cadence'.
    :param treatment: the input treatment where the lower and upper cadences are to be added
    :param tokens: token stream not yet parsed
    :return: the tail of tokens not consumed by this parse and the input treatment enhanced by the cadence parsed
    """
    tokens = expect(TokenType.Slash, tokens)
    tokens, lower_cadence = parse_cadence(tokens)
    # Note: An Integer cannot be less than 0.
    tokens = expect(TokenType.Minus, tokens)
    tokens, upper_cadence = parse_cadence(tokens)
    if lower_cadence > upper_cadence:
        error("Lower cadence exceeds upper cadence.")
    treatment.lower_cadence = lower_cadence
    treatment.upper_cadence = upper_cadence
    return tokens, treatment


def parse_cadence(tokens: List[Token]) -> (List[Token], int):
    """
    Parses given tokens according to the rule 'Integer "c" | "C")'.
    :param tokens: token stream not yet parsed
    :return: the tail of tokens not consumed by this parse and the cadence parsed
    """
    if tokens[0].type == TokenType.Integer:
        value: int = int(tokens[0].value)
        tokens = expect(TokenType.Cadence, tokens[1:])
        return tokens, value
    else:
        error("Integer expected.")


def parse_ftp(tokens: List[Token]) -> (List[Token], int):
    """
    Parses given tokens according to the rule '"|" Integer WUnit'.
    :param tokens: token stream not yet parsed
    :return: the tail of tokens not consumed by this parse and the FTP value parsed
    """
    tokens = expect(TokenType.Pipe, tokens)
    if tokens[0] != TokenType.Integer:
        expect(TokenType.Integer, tokens)
    value: int = int(tokens[0].value)
    return expect(TokenType.Watt, tokens[1:]), value


def unparse(tokens: List[Token]) -> None:
    """
    Emits the given tokens in human-readable form to standard output.
    :param tokens: token stream to be emitted
    :return: None
    """
    for token in tokens:
        match token.type:
            case TokenType.Float:
                print(token.value, end=' ')
                # print(f'<{token.type.value}, {str(token.value)}>', end=' ')
            case TokenType.Integer:
                print(int(token.value), end=' ')
                # print(f'<{token.type.value}, {str(int(token.value))}>', end=' ')
            case TokenType.End:
                pass
            case _:
                print(token.type.value, end=' ')
    print("")


def error(message: str) -> None:
    """
    Prints the given message and then the usage information and
    finally exits with an error code.
    :param message: message to be emitted to standard output
    :return: None
    """
    print(message)
    usage()
    sys.exit(1)


def tokenize(input_data: str) -> List[Token]:
    """
    Runs the lexical analysis on input_data and yields the corresponding tokens.
    :param input_data: the input data to be tokenized
    :return: the token stream for input_data
    """
    result: List[Token] = []
    index: int = 0
    while index < len(input_data):
        if input_data[index] in string.whitespace:
            index = index + 1
        elif input_data[index].isdigit():
            # beginning of a number; could be integer or float
            start: int = index
            while index < len(input_data) and input_data[index].isdigit():
                index = index + 1
            if input_data[index] == '.':
                # the number is a float
                index = index + 1
                # continue with the digits behind the period
                while index < len(input_data) and input_data[index].isdigit():
                    index = index + 1
                value: float = float(input_data[start:index])
                result.append(Token(TokenType.Float, value))
            else:
                value: int = int(input_data[start:index])
                result.append(Token(TokenType.Integer, value))
        else:
            match input_data[index]:
                case '+':
                    result.append(Token(TokenType.Plus))
                case '-':
                    result.append(Token(TokenType.Minus))
                case '*':
                    result.append(Token(TokenType.Multiply))
                case '(':
                    result.append(Token(TokenType.OpeningBracket))
                case ')':
                    result.append(Token(TokenType.ClosingBracket))
                case '|':
                    result.append(Token(TokenType.Pipe))
                case '@':
                    result.append(Token(TokenType.At))
                case '/':
                    result.append(Token(TokenType.Slash))
                case 'w' | 'W':
                    result.append(Token(TokenType.Watt))
                case 'c' | 'C':
                    result.append(Token(TokenType.Cadence))
                case 'h' | 'H':
                    result.append(Token(TokenType.Hour))
                case 'm' | 'M':
                    result.append(Token(TokenType.Minute))
                case 's' | 's':
                    result.append(Token(TokenType.Second))
                case '_':
                    result.append(Token(TokenType.DontCare))
                case _:
                    print(input_data[index:])
                    error(f"Unrecognized character '{input_data[index]}'")
            index = index + 1
    result.append(Token(TokenType.End))
    return result


def read(filename: str) -> str:
    """
    Reads and returns the content of the file with given filename.
    :param filename: name of the file to be read
    :return: the content of the file
    """
    if not exists(filename):
        error(f"Input file '{filename}' does not exist.")

    try:
        with open(filename) as file:
            return file.read()
    except Exception as e:
        error(f"Cannot read input file '{filename}': {e}.")


def usage() -> None:
    """
    Prints the version and usage message.
    :return: None
    """
    print(f'This is version {VERSION}.')
    print('Usage: ' + sys.argv[
        0] + ' [-h] [-f] [-a <author> ] [-d <description>] -n <name> (-i <inputfile> | -w <workout>) -o <outputfile>')
    print('  -h or --help: prints this message and exits; is optional')
    print('  -f or --force: an existing output file will be overridden; is optional')
    print('  -a or --author: declares the author of the workout; is optional')
    print('  -d or --description: the description of the workout; is optional')
    print('  -n or --name: the unique name of the workout; is mandatory')
    print('  -i or --input: name of the file containing a workout specification; is mandatory unless -w is used')
    print('  -w or --workout: workout specification; mandatory unless -i is used')
    print('  -o or --output: name of the Zwift workout file to be created; must have file extension .zwo; is mandatory')


def main(argv) -> None:
    """
    Main program processing the script arguments and then starting the Zwift workout generation.
    :param argv: command-line arguments passed by the user of this script
    :return: None
    """
    input_file: str = ''
    output_file: str = ''
    force: bool = False
    workout: str = ''
    author: str = ''
    description: str = ''
    name: str = ''

    try:
        opts, args = getopt.getopt(argv, "hfi:w:o:a:d:n:",
                                   ["help", "force", "input=", "workout=", "output=", "author=", "description=",
                                    "name="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-f", "--force"):
            force = True
        elif opt in ("-i", "--input"):
            input_file = arg
        elif opt in ("-o", "--output"):
            output_file = arg
        elif opt in ("-w", "--workout"):
            workout = arg
        elif opt in ("-a", "--author"):
            author = arg
        elif opt in ("-d", "--description"):
            description = arg
        elif opt in ("-n", "--name"):
            name = arg
        else:
            error(f'Unknown option {opt}.')

    if output_file == '':
        error("No output file given.")
    if not output_file.lower().endswith('.zwo'):
        error("Zwift workout files must have the extension '.zwo'.")

    if (workout != '' and input_file != '') or (workout == '' and input_file == ''):
        error("Either a workout or an input file must be specified.")
    if name == '':
        error('A name for the workout must be specified.')

    if input_file != "":
        workout = read(input_file)

    if workout == '':
        error("Workout specification must not be empty.")

    if description == '':
        description = workout

    if not force and exists(output_file):
        error(f"Output file '{output_file}' exists already and would be overridden. Delete it first.")

    with open(output_file, 'w') as file:
        process(file, workout, author, description, name)


if __name__ == '__main__':
    """
    Runs main with the command-line arguments passed by the user to this script.
    """
    main(sys.argv[1:])
