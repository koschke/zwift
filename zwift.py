# This program transforms a simple textual bike workout description into
# a Zwift workout.
#
# The input must conform to the following grammar (specified in EBNF):
#  Workout ::= Stages FTP .
#  Stages  ::= Stage ("+" Stage)* .
#  Stage   ::= Integer "*" "(" Stages ")") | Time "@" Watts .
#  Time    ::= (Integer | Float) TUnit .
#  Watts   ::= "_" | Integer WUnit ("-" Integer WUnit)? .
#  FTP     ::= "|" Integer WUnit .
#  WUnit   ::= ("w" | "W") .
#  TUnit   ::= ("m" | "M" | "s" | "S" | "h" | "H") .
#  Integer ::= ["0"-"9"]+ .
#  Float   ::= ["0"-"9"]+ "." ["0"-"9"]*.

import string
import sys
import getopt
import typing
from enum import Enum
from typing import List
from datetime import timedelta
from os.path import exists

class TokenType(str, Enum):
    Plus = "+"
    Minus = "-"
    Multiply = "*",
    OpeningBracket = "(",
    ClosingBracket = ")",
    Pipe = "|",
    At = "@",
    Float = "Float",
    Integer = "Integer",
    Watt = "w",
    Hour = "h",
    Minute = "m",
    Second = "s",
    DontCare = "_",
    End = "<EndOfinput>"


class Token:
    type: TokenType
    value: float

    def __init__(self, t: TokenType, value: float = 0):
        self.type = t
        self.value = value


class Treatment:
    seconds: float

    def __str__(self) -> str:
        return "ABSTRACT_TREATMENT()"

    def to_zwift(self, file: typing.TextIO, ftp: float) -> None:
        print("", file=file)


class Free(Treatment):
    def __str__(self) -> str:
        return f"free({str(self.seconds)}s)"

    def to_zwift(self, file: typing.TextIO, ftp: float) -> None:
        print(f"     <Freeride Duration=\"{self.seconds}\"/>", file=file)


class Power(Treatment):
    wattage: int

    def __init__(self, value: int):
        self.wattage = value

    def __str__(self) -> str:
        return f"power({str(self.seconds)}s, {str(self.wattage)}w)"

    def to_zwift(self, file: typing.TextIO, ftp: float) -> None:
        print(f"     <SteadyState Duration=\"{self.seconds}\" Power=\"{relative(self.wattage, ftp)}\" pace=\"0\"/>",
              file=file)


def relative(wattage: float, ftp: float) -> float:
    return round(wattage / ftp, 2)


class Range(Treatment):
    start_wattage: int
    end_wattage: int

    def __init__(self, start: int, end: int):
        self.start_wattage = start
        self.end_wattage = end

    def __str__(self):
        return f"power({str(self.seconds)}s, {str(self.start_wattage)}w-{str(self.end_wattage)}w)"

    def to_zwift(self, file: typing.TextIO, ftp: float) -> None:
        if self.start_wattage <= self.end_wattage:
            print(f"     <Warmup Duration=\"{self.seconds}\" PowerLow=\"{relative(self.start_wattage, ftp)}\""
                  + f" PowerHigh=\"{relative(self.end_wattage, ftp)}\" pace=\"0\"/>",
                  file=file)
        else:
            print(f"     <Cooldown Duration=\"{self.seconds}\" PowerLow=\"{relative(self.end_wattage, ftp)}\""
                  + f" PowerHigh=\"{relative(self.start_wattage, ftp)}\" pace=\"0\"/>",
                  file=file)


def expect(token: TokenType, tokens: List[Token]) -> List[Token]:
    if tokens[0].type != token:
        unparse(tokens)
        error(f'{token.value} expected')
    return tokens[1:]


def expect_one_of(expected: list[TokenType], tokens: list[Token]) -> list[Token]:
    if tokens[0].type not in expected:
        unparse(tokens)
        error(f'One of {[t.value for t in expected]} expected')
    return tokens[1:]


def process(file: typing.TextIO, workout: str, author: str, description: str, name: str) -> None:
    tokens: list[Token] = tokenize(workout)
    program: list[Treatment]
    # unparse(tokens)
    ftp: float
    tokens, program, ftp = parse(tokens)
    if tokens[0].type != TokenType.End:
        unparse(tokens)
        error("There is superfluous input.")
    print(f'Total time of the workout is {str(timedelta(seconds=total_time(program)))} h.')
    to_zwift(file, program, ftp, author, description, name)

def total_time(program: list[Treatment]) -> float:
    sum: float = 0
    for t in program:
        sum = sum + t.seconds
    return sum

def to_zwift(file: typing.TextIO, program: list[Treatment], ftp: float, author: str, description: str,
             name: str) -> None:
    preamble(file, author, name, description)
    for treatment in program:
        treatment.to_zwift(file, ftp)
    postamble(file)


def preamble(file: typing.TextIO, author: str, name: str, description: str) -> None:
    print("<workout_file>", file=file)
    print(f"  <author>{author}</author>", file=file)
    print(f"  <name>{name}</name>", file=file)
    print(f"  <description>{description}</description>", file=file)
    print("   <sportType>bike</sportType>", file=file)
    print("   <tags></tags>", file=file)
    print("   <workout>", file=file)


def postamble(file: typing.TextIO) -> None:
    print("   </workout>", file=file)
    print("</workout_file>", file=file)


def parse(tokens: List[Token]) -> (List[Token], List[Treatment], float):
    program: List[Treatment]
    tokens, program = parse_stages(tokens)
    ftp: float
    tokens, ftp = parse_ftp(tokens)
    return tokens, program, ftp


def parse_stages(tokens: List[Token]) -> (List[Token], List[Treatment]):
    program: list[Treatment]
    tokens, program = parse_stage(tokens)
    while tokens[0].type == TokenType.Plus:
        stage: list[Treatment]
        tokens, stage = parse_stage(tokens[1:])
        program = program + stage
    return tokens, program


def parse_stage(tokens: List[Token]) -> (List[Token], List[Treatment]):
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
        tokens, treatment = parse_watts(tokens)
        treatment.seconds = seconds
        return tokens, [treatment]
    else:
        unparse(tokens)
        error("Number expected.")


def parse_time(tokens: list[Token]) -> (list[Token], int):
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


def parse_watts(tokens: List[Token]) -> (List[Token], Treatment):
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


def parse_ftp(tokens: List[Token]) -> (List[Token], int):
    tokens = expect(TokenType.Pipe, tokens)
    if tokens[0] != TokenType.Integer:
        expect(TokenType.Integer, tokens)
    value: int = int(tokens[0].value)
    return expect(TokenType.Watt, tokens[1:]), value


def unparse(tokens: List[Token]):
    for token in tokens:
        match token.type:
            case TokenType.Float:
                print(f'<{token.type.value}, {str(token.value)}>', end=' ')
            case TokenType.Integer:
                print(f'<{token.type.value}, {str(int(token.value))}>', end=' ')
            case _:
                print(token.type.value, end=' ')
    print("")


def error(message: str):
    print(message)
    usage()
    sys.exit()


def tokenize(inputdata: str) -> List[Token]:
    result: List[Token] = []
    index: int = 0
    while index < len(inputdata):
        # print(f'input: {inputdata[index]}')
        if inputdata[index] in string.whitespace:
            index = index + 1
        elif inputdata[index].isdigit():
            # beginning of a number; could be integer or float
            start: int = index
            while (index < len(inputdata) and inputdata[index].isdigit()):
                index = index + 1
            if inputdata[index] == '.':
                # the number is a float
                index = index + 1
                # continue with the digits behind the period
                while (index < len(inputdata) and inputdata[index].isdigit()):
                    index = index + 1
                value: float = float(inputdata[start:index])
                result.append(Token(TokenType.Float, value))
            else:
                value: int = int(inputdata[start:index])
                result.append(Token(TokenType.Integer, value))
        else:
            match inputdata[index]:
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
                case 'w' | 'W':
                    result.append(Token(TokenType.Watt))
                case 'h' | 'H':
                    result.append(Token(TokenType.Hour))
                case 'm' | 'M':
                    result.append(Token(TokenType.Minute))
                case 's' | 's':
                    result.append(Token(TokenType.Second))
                case '_':
                    result.append(Token(TokenType.DontCare))
                case _:
                    error(f"Unrecognized character '{inputdata[index]}'")
            index = index + 1
    result.append(Token(TokenType.End))
    return result


def read(filename: str) -> str:
    if not exists(filename):
        error(f"Input file '{filename}' does not exist.")

    try:
        with open(filename) as file:
            return file.read()
    except:
        error(f"Cannot read input file '{filename}'.")


def usage() -> None:
    print(
        sys.argv[0] + ' [-a <author> ] [-d <description>] [-n <name>] (-i <inputfile> | -w <workout>) -o <outputfile>')


def main(argv):
    input_file: str = ''
    output_file: str = ''
    workout: str = ''
    author: str = ''
    description: str = ''
    name: str = ''

    try:
        opts, args = getopt.getopt(argv, "hi:w:o:a:d:n:",
                                   ["help", "input=", "workout=", "output=", "author=", "description=", "name="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        #print(f'opt: "{opt}" arg:"{arg}"')
        if opt == '-h':
            usage()
            sys.exit()
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
    if output_file == '':
        error("No output file given.")
    if (workout != '' and input_file != '') or (workout == '' and input_file == ''):
        error("Either a workout or an input file must be specified.")
    if name == '':
        error('A name for the workout must be specified.')

    #print(f'Given workout is "{workout}"')
    #print(f'Input file is "{input_file}"', )
    #print(f'Output file is "{output_file}"')

    if input_file != "":
        workout = read(input_file)
        #print(f'Read workout is "{workout}"')

    if workout == '':
        error("Workout specification must not be empty.")

    with open(output_file, 'w') as file:
        process(file, workout, author, description, name)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main(sys.argv[1:])
