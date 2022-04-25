#!/usr/bin/env python3
# -*- coding: utf-8 -*-


#######################################
# Interpreter for language IPPcode22  #
# Author: Adam Balušeskul             #
# login: xbalus01                     #
#######################################

import sys
import re
import xml.etree.ElementTree as Xml


class ParamsError(Exception):
    """missing script parameter (if necessary) or use of forbidden combination of parameters"""


class FileOpenError(Exception):
    """couldn't open input files (e.g. file doesn't exist, you don't have required permissions etc.)"""


class XMLFormatError(Exception):
    """wrong XML format within input file (file isn't well-formed)"""


class UnexpectedXMLStructure(Exception):
    """unexpected XML structure (e.g. instruction with a duplicate order)"""


class SemanticsError(Exception):
    """wrong semantics of input code (e.g. usage of an undefined label, variable redefinition etc.)"""


class OperandsError(Exception):
    """runtime error - wrong operand types"""


class NonexistentVarError(Exception):
    """runtime error - variable does not exist"""


class NonexistentFrameError(Exception):
    """runtime error - frame does not exist"""


class MissingValError(Exception):
    """runtime error - missing value (in variable, on data stack or in call stack)"""


class OperandValError(Exception):
    """runtime error - wrong operand value (e.g. division by zero, wrong return value of instruction EXIT etc.)"""


class StringError(Exception):
    """runtime error - string manipulation error"""


class InternalError(Exception):
    """internal script error"""


# Global Frame, Local Frame, Temporary Frame
GF = {}
LF = None
TF = None
# Frame Stack, Call Stack, Data Stack
FS = []
CS = []
DS = []
# Label dictionary - stores labels
LD = {}

zero_arg_instr_list = ["CREATEFRAME", "PUSHFRAME", "POPFRAME", "RETURN", "BREAK"]
one_arg_instr_list = ["DEFVAR", "POPS", "LABEL", "CALL", "JUMP", "PUSHS", "WRITE", "EXIT", "DPRINT"]
two_arg_instr_list = ["MOVE", "INT2CHAR", "STRLEN", "TYPE", "NOT", "READ"]
three_arg_instr_list = ["ADD", "SUB", "MUL", "IDIV", "LT", "GT", "EQ", "AND", "OR", "CONCAT",
                        "GETCHAR", "SETCHAR", "STRI2INT", "JUMPIFEQ", "JUMPIFNEQ"]
var_types = ["int", "string", "bool", "nil"]


def raise_err(err):
    """
    attaches correct error message to given error and raises the error

    :param err: type of error
    """
    msg = ""
    if err == ParamsError:
        msg = "missing script parameter (if necessary) or use of forbidden combination of parameters"
    elif err == XMLFormatError:
        msg = "wrong XML format within input file (file isn't well-formed)"
    elif err == UnexpectedXMLStructure:
        msg = "unexpected XML structure (e.g. instruction with a duplicate order)"
    elif err == SemanticsError:
        msg = "wrong semantics of input code"
    elif err == OperandsError:
        msg = "wrong operand types"
    elif err == NonexistentVarError:
        msg = "runtime error - variable does not exist"
    elif err == NonexistentFrameError:
        msg = "runtime error - frame does not exist"
    elif err == MissingValError:
        msg = "runtime error - missing value (in variable, on data stack or in call stack)"
    elif err == OperandValError:
        msg = "runtime error - wrong operand value (e.g. division by zero, wrong return value of instruction EXIT etc.)"
    elif err == StringError:
        msg = "runtime error - string manipulation error"
    elif err == InternalError:
        msg = "internal program error"
    raise err(msg)


def exit_err(err_type, msg):
    """
    exits the program with the correct return value and a fitting error message

    :param err_type: type of error
    :param msg: error message
    """
    err_num = 0
    if err_type == ParamsError:
        err_num = 10
    elif err_type == FileOpenError:
        msg = "couldn't open input files (file probably doesn't exist or you don't have required permissions)"
        err_num = 11
    elif err_type == XMLFormatError:
        err_num = 31
    elif err_type == UnexpectedXMLStructure:
        err_num = 32
    elif err_type == SemanticsError:
        err_num = 52
    elif err_type == OperandsError:
        err_num = 53
    elif err_type == NonexistentVarError:
        err_num = 54
    elif err_type == NonexistentFrameError:
        err_num = 55
    elif err_type == MissingValError:
        err_num = 56
    elif err_type == OperandValError:
        err_num = 57
    elif err_type == StringError:
        err_num = 58
    elif err_type == InternalError:
        err_num = 99
    print("Error: {0}".format(msg), file=sys.stderr)
    sys.exit(err_num)


def print_help():
    """
    prints help on how to run the interpreter and what it does
    """
    print("""
INTERPRETER for language IPPcode22 Help Guide

Script (interpret.py in Python 3.8 programming language) loads XML representation of a program (in IPPcode22), 
interprets this program using inputs specified by command line parameters and generates output.

Usage: python3.8 interpret.py [OPTION]

OPTIONS - when launching script, user must include either source file or input file (or both)!

--help
print this help and exit

--source=file
input file with an XML representation of a source code

--input=file
file with inputs used for interpretation of a specified source code
""")


def composed_of_whitespace(x):
    """
    checks and returns if input string is composed of
    whitespace characters only
    """
    if x is not None:
        if re.search("\S+", x):
            return False
    return True


def process_esc_seq_in_str(string):
    """
    replaces escape sequences with actual characters in given string

    :return: string with escape sequences replaced
    """
    if not string:
        return ""
    for i in range(0, 999):
        string = string.replace("\\{:03}".format(i), chr(i))
    return string


def check_root_attrib(root):
    """
    checks XML correctness of the main program

    :param root: main program root composed of instructions
    """
    if root.tag != 'program':
        raise_err(UnexpectedXMLStructure)

    root_size = len(root.attrib)
    if 1 > root_size > 3 or not composed_of_whitespace(root.text):
        raise_err(UnexpectedXMLStructure)
    # check if root has an attribute "language" and if it has more attributes, if they are "name" or "description"
    if "language" not in root.attrib or root.get("language").upper() != "IPPCODE22" or \
            (root_size == 2 and ("name" not in root.attrib and "description" not in root.attrib)) or \
            (root_size == 3 and ("name" not in root.attrib or "description" not in root.attrib)):
        raise_err(UnexpectedXMLStructure)


def check_arg_xml(argc, instr):
    """
    checks XML format of instruction arguments

    :param argc: number of arguments
    :param instr: instruction to check
    """
    arg_list = ["arg1", "arg2", "arg3"]
    for i in range(argc):
        curr_arg = instr[i]
        if curr_arg.tag != arg_list[i]:
            raise_err(UnexpectedXMLStructure)
        if not composed_of_whitespace(curr_arg.tail):
            raise_err(UnexpectedXMLStructure)
        if "type" not in curr_arg.attrib or len(curr_arg.attrib) != 1 or len(curr_arg) != 0:
            raise_err(UnexpectedXMLStructure)


def check_instr_xml(root):
    """
    checks XML format of root instructions and their arguments

    :param root: main program composed of instructions
    """
    for instr in root:
        i_opcode = instr.attrib.get("opcode").upper()
        argc = len(list(instr))

        if not composed_of_whitespace(instr.text) or not composed_of_whitespace(instr.tail):
            raise_err(UnexpectedXMLStructure)
        if instr.tag != "instruction":
            raise_err(UnexpectedXMLStructure)

        # check correct argument count depending on instruction opcode
        if i_opcode in zero_arg_instr_list and argc != 0 or \
                i_opcode in one_arg_instr_list and argc != 1 or \
                i_opcode in two_arg_instr_list and argc != 2 or \
                i_opcode in three_arg_instr_list and argc != 3:
            raise_err(UnexpectedXMLStructure)
        check_arg_xml(argc, instr)


def check_symb_sem(arg, arg_type, type_to_check):
    """
    if given argument type is semantically correct <symb> type, function
    returns the value of that argument depending on its specific
    type defined by the user (e.g. "int","string",..)

    :param arg: instruction argument
    :param arg_type: program-given argument type
    :param type_to_check: user-given argument type
    """
    if (arg_type != type_to_check) and (arg_type != "var"):
        raise_err(OperandsError)
    if arg_type == "var":
        var = get_or_update_var(arg, None, False)
        if var[0] not in var_types:
            raise_err(MissingValError)
        if var[0] != type_to_check:
            raise_err(OperandsError)
        elif var[0] == "int":
            return int(var[1])
        elif var[0] == "string":
            return process_esc_seq_in_str(var[1])
        elif var[0] == "bool":
            return var[1]
    elif arg_type == "int":
        return int(arg.text)
    elif arg_type == "string":
        return process_esc_seq_in_str(arg.text)
    elif arg_type == "bool":
        return arg.text


def handle_args():
    """
    handles program arguments - checks for interpreter input/source or potentially both of them
    or prints help

    :return: (src, inp): tuple of source file and input file
    """
    if len(sys.argv) == 2:
        # looking for either help, source or input in a program argument
        arg = sys.argv[1]
        help_found = re.search("^(--h|--help)$", arg)
        source_found = re.search("^--source=.*$", arg)
        input_found = re.search("^--input=.*$", arg)
        if help_found:
            print_help()
            sys.exit(0)
        elif source_found:
            src = re.split("--source=", arg)[1]
            return src, None
        elif input_found:
            inp = re.split("--input=", arg)[1]
            return None, inp

    elif len(sys.argv) == 3:
        src = None
        inp = None
        # looking for both source and input in program arguments
        for arg in sys.argv:
            src_search = re.search("^--source=.*$", arg)
            inp_search = re.search("^--input=.*$", arg)
            if src_search is not None:
                src = re.split("--source=", src_search.group())[1]
            if inp_search is not None:
                inp = re.split("--input=", inp_search.group())[1]
        if src and inp:
            return src, inp
        else:
            raise_err(ParamsError)
    else:
        raise_err(ParamsError)


def fill_label_dict_with_labels(root):
    """
    attaches program labels with their correct positions and stores
     them in the label dictionary
    """
    global LD
    count = 0
    for instr in root:
        opcode = instr.get("opcode").upper()
        if opcode == "LABEL":
            arg = instr[0]
            if arg.text in LD:  # label is already defined
                raise_err(SemanticsError)
            LD[arg.text] = count  # adds {"label": order} into label dict
        count += 1


def print_interpreter_status(iip, executed_i):
    """
    prints statuses of main elements of the program on standard error output

    :param iip: internal instruction pointer
    :param executed_i: number of executed instructions
    """
    global GF, LF, TF, FS, CS, DS
    print(
        """
----------------------------------------
Position in code: {0}
----------------------------------------
Number of executed instructions: {1}
----------------------------------------
Global Frame
{2}
----------------------------------------
Local Frame
{3}
----------------------------------------
Temporary Frame
{4}
----------------------------------------
Frame Stack
{5}
----------------------------------------
Call Stack
{6}
----------------------------------------
Data Stack
{7}
----------------------------------------
""".format(iip, executed_i, GF, LF, TF, FS, CS, DS, file=sys.stderr)
    )


def check_in_frame(frame, var):
    if frame is None and frame != GF:
        raise_err(NonexistentFrameError)
    if var not in frame:
        raise_err(NonexistentVarError)


def check_not_in_frame(frame, var):
    if frame is None and frame != GF:
        raise_err(NonexistentFrameError)
    if var in frame:
        raise_err(SemanticsError)


def define_var(arg):
    """
    defines variable in frame determined by the argument

    :param arg: instruction argument
    """
    global LF, TF, GF
    frame = arg.text.split("@")[0]
    var = arg.text.split("@")[1]
    if frame == "LF":
        check_not_in_frame(LF, var)
        LF[var] = ["", ""]
    elif frame == "TF":
        check_not_in_frame(TF, var)
        TF[var] = ["", ""]
    elif frame == "GF":
        check_not_in_frame(GF, var)
        GF[var] = ["", ""]


def check_is_var_defined(arg):
    """
    check if a variable is defined in frame determined by the argument

    :param arg: instruction argument
    """
    global LF, TF, GF
    frame = arg.text.split("@")[0]
    var = arg.text.split("@")[1]
    if frame == "LF":
        check_in_frame(LF, var)
    elif frame == "TF":
        check_in_frame(TF, var)
    elif frame == "GF":
        check_in_frame(GF, var)


def get_or_update_var(arg, val, to_update):
    """
    if to_update is True: updates a variable in frame with a user-given value
    if to_update is False: returns a variable from frame

    :param arg: instruction argument
    :param val: value to update the frame with
    :param to_update: decides if function should update or get value
    """
    global DS, GF, LF, TF
    frame = arg.text.split("@")[0]
    var = arg.text.split("@")[1]

    if frame == "LF":
        check_in_frame(LF, var)
        if to_update:
            LF[var] = [val[0], val[1]]
        else:
            val = LF.get(var)
    elif frame == "TF":
        check_in_frame(TF, var)
        if to_update:
            TF[var] = [val[0], val[1]]
        else:
            val = TF.get(var)
    elif frame == "GF":
        check_in_frame(GF, var)
        if to_update:
            GF[var] = [val[0], val[1]]
        else:
            val = GF.get(var)
    if not to_update:
        return val


def write_var(arg, arg_type, write_on_err):
    """
    writes a variable on user-decided output depending on its type

    :param arg: instruction argument
    :param arg_type: type of argument
    :param write_on_err: if True, function writes on standard error output, otherwise on standard output
    """
    if arg_type == "nil":
        var_value = ""
    elif arg_type == "var":
        val = get_or_update_var(arg, None, False)
        is_nonempty(val)
        if val[0] == "nil":
            var_value = ""
        else:
            var_value = val[1]
    elif arg_type == "string":
        var_value = process_esc_seq_in_str(arg.text)
    else:
        var_value = arg.text
    print(var_value, file=sys.stderr, end='') if write_on_err else print(var_value, end='')


def zero_arg_instructions_eval(i_opcode, iip, executed_i):
    """
    processes instructions that have zero arguments

    :param i_opcode: instruction opcode
    :param iip: internal instruction pointer
    :param executed_i: number of executed instructions
    :return: None on failure
    """
    global TF, FS, CS, LF
    if i_opcode == "CREATEFRAME":
        TF = {}
    elif i_opcode == "PUSHFRAME":
        if TF is None:
            raise_err(NonexistentFrameError)
        if TF is not None:
            LF = dict(TF)
        FS.append(LF)
        TF = None
    elif i_opcode == "POPFRAME":
        if LF is None or not FS:
            raise_err(NonexistentFrameError)
        TF = FS.pop()
        if FS:
            LF = FS[-1]
        else:
            LF = None
    elif i_opcode == "RETURN":
        if not CS:
            raise_err(MissingValError)
        iip = int(CS.pop()) - 1
    elif i_opcode == "BREAK":
        print_interpreter_status(iip, executed_i)
    else:
        return None
    return iip


def exit_instr(arg, arg_type):
    exit_code = check_symb_sem(arg, arg_type, "int")
    if 0 <= exit_code <= 49:
        sys.exit(exit_code)
    else:
        raise_err(OperandValError)


def eval_jump(arg, iip):
    if arg.text in LD:
        iip = int(LD.get(arg.text)) - 1
    else:
        raise_err(SemanticsError)
    return iip


def one_arg_instructions_eval(instr, i_opcode, iip):
    """
    processes instructions that have one argument

    :param instr: current instruction
    :param i_opcode: instruction opcode
    :param iip: internal instruction pointer
    :return: None on failure
    """
    global CS, DS
    arg = instr[0]
    arg_type = arg.get("type")
    if i_opcode == "DEFVAR":
        define_var(arg)
    elif i_opcode == "CALL":
        CS.append(iip + 1)
        iip = eval_jump(arg, iip)
    elif i_opcode == "JUMP":
        iip = eval_jump(arg, iip)
    elif i_opcode == "PUSHS":
        if arg_type == "var":
            val = get_or_update_var(arg, None, False)
            is_nonempty(val)
            DS.append(val)
        else:
            DS.append([arg_type, arg.text])
    elif i_opcode == "POPS":
        if not DS:
            raise_err(MissingValError)
        val = DS.pop()
        get_or_update_var(arg, val, True)
    elif i_opcode == "WRITE":
        write_var(arg, arg_type, False)
    elif i_opcode == "EXIT":
        exit_instr(arg, arg_type)
    elif i_opcode == "DPRINT":
        write_var(arg, arg_type, True)
    elif i_opcode == "LABEL":
        pass
    else:
        return None
    return iip


def read(to_update, var_type, input_file):
    """
    reads from user-specified input file and saves the read variable

    :param to_update: variable to save to
    :param var_type: type of variable to save
    :param input_file: input file
    """
    if input_file is None:
        user_input = input()
    else:
        user_input = input_file.readline()
        user_input = "nil" if user_input == '' else user_input.strip()  # empty file

    actual_type = var_type.text
    if user_input == "nil":
        pass
    elif actual_type == "int":
        user_input = int(user_input) if re.search("^[+-]?[0-9]*$", user_input) else "nil"
    elif actual_type == "bool":
        user_input = "true" if re.search("^true$", user_input, flags=re.I) else "false"
    elif actual_type == "string":
        pass
    elif actual_type == "nil":
        user_input = "nil"
    else:
        raise_err(SemanticsError)
    to_make = var_type.text if user_input != "nil" else "nil"
    get_or_update_var(to_update, [to_make, user_input], True)


def type_eval(arg1, arg2, arg2_type):
    if arg2_type == "var":
        var_type = get_or_update_var(arg2, None, False)[0]
    else:
        var_type = arg2_type
    var = ["string", var_type]
    get_or_update_var(arg1, var, True)


def not_eval(var, symb, symb_type):
    """
    processes NOT instruction - negates the value of input boolean

    :param var: stores the result of NOT operation
    :param symb: symbol to execute the NOT operation on
    :param symb_type: type of the symbol
    """
    val = []
    if symb_type == "var":
        val = get_or_update_var(symb, None, False)
        is_nonempty(val)
        if val[0] != "bool":
            raise_err(OperandsError)
    elif symb_type == "bool":
        val = [symb_type, symb.text]
    else:
        raise_err(OperandsError)
    if val[1] == "true":
        val[1] = "false"
    else:
        val[1] = "true"
    get_or_update_var(var, val, True)


def int_to_char_eval(var, symb, symb_type):
    """
    converts symbol <symb> to char and stores into variable <var>

    :param var: variable to store char to
    :param symb: symbol to convert to char
    :param symb_type: type of symbol
    """
    max_ascii_val = 1114111
    int_val = check_symb_sem(symb, symb_type, "int")
    if not (0 < int_val < max_ascii_val):
        raise_err(StringError)
    get_or_update_var(var, ["string", chr(int_val)], True)


def is_nonempty(val):
    if val[0] not in var_types:
        raise_err(MissingValError)


def two_arg_instructions_eval(instr, i_opcode, iip, input_file):
    """
    processes instructions that have two arguments

    :param instr: current instruction
    :param i_opcode: instruction opcode
    :param iip: internal instruction pointer
    :param input_file: input file

    :return: None on failure
    """
    global GF, TF, LF, FS, CS, DS, LD
    arg1 = instr[0]
    arg2 = instr[1]
    arg2_type = arg2.get("type")
    if i_opcode in two_arg_instr_list:
        check_is_var_defined(arg1)
    if i_opcode == "MOVE":
        val = get_or_update_var(arg2, None, False) if arg2_type == "var" else [arg2_type, arg2.text]
        is_nonempty(val)
        get_or_update_var(arg1, val, True)
    elif i_opcode == "INT2CHAR":
        int_to_char_eval(arg1, arg2, arg2_type)
    elif i_opcode == "READ":
        read(arg1, arg2, input_file)
    elif i_opcode == "STRLEN":
        str_len = len(check_symb_sem(arg2, arg2_type, "string"))
        get_or_update_var(arg1, ["int", str_len], True)
    elif i_opcode == "TYPE":
        type_eval(arg1, arg2, arg2_type)
    elif i_opcode == "NOT":
        not_eval(arg1, arg2, arg2_type)
    else:
        return None
    return iip


def arithmetic_operations_eval(i_opcode, symb1, symb1_type, symb2, symb2_type):
    """
    evaluates arithmetic operations ADD, SUB, MUL, IDIV

    :param i_opcode: instruction opcode
    :param symb1: operator 1
    :param symb1_type: type of op1
    :param symb2: operator 2
    :param symb2_type: type of op2
    :return: evaluation result
    """
    result = None
    n1 = check_symb_sem(symb1, symb1_type, "int")
    n2 = check_symb_sem(symb2, symb2_type, "int")
    if i_opcode == "ADD":
        result = n1 + n2
    elif i_opcode == "SUB":
        result = n1 - n2
    elif i_opcode == "MUL":
        result = n1 * n2
    elif i_opcode == "IDIV":
        if n2 == 0:
            raise_err(OperandValError)
        result = n1 // n2
    return result


def bool_operations_eval(i_opcode, symb1, symb1_type, symb2, symb2_type):
    """
    evaluates boolean operations AND, OR

    :param i_opcode: instruction opcode
    :param symb1: operator 1
    :param symb1_type: type of op1
    :param symb2: operator 2
    :param symb2_type: type of op2
    :return: evaluation result
    """
    b1 = check_symb_sem(symb1, symb1_type, "bool")
    b2 = check_symb_sem(symb2, symb2_type, "bool")
    result = None
    if i_opcode == "AND":
        result = "true" if b1 == "true" and b2 == "true" else "false"
    elif i_opcode == "OR":
        result = "true" if b1 == "true" or b2 == "true" else "false"
    return result


def get_char_in_string_on_pos(arg2, arg2_type, arg3, arg3_type):
    """
    returns the character in string on given position
    """
    arg_str = check_symb_sem(arg2, arg2_type, "string")
    arg_pos = check_symb_sem(arg3, arg3_type, "int")
    if 0 > arg_pos or arg_pos >= len(arg_str):
        raise_err(StringError)
    return arg_str[arg_pos]


def concat_eval(symb1, symb1_type, symb2, symb2_type):
    """
    concatenates two strings (evaluation of operation CONCAT)

    :param symb1: string 1
    :param symb1_type: type of op1
    :param symb2: string 2
    :param symb2_type: type of op2
    :return: concatenated strings
    """
    s1 = check_symb_sem(symb1, symb1_type, "string")
    s2 = check_symb_sem(symb2, symb2_type, "string")
    if s1 is None or s2 is None:
        return ""
    s = s1 + s2
    return s


def set_char_eval(var, symb1, symb1_type, symb2, symb2_type):
    """
    evaluates operation SETCHAR

    :param var: string containing char to modify
    :param symb1: position in string
    :param symb1_type: type of symbol 1
    :param symb2: char to modify to
    :param symb2_type: type of symbol 2
    :return: evaluation result
    """
    to_replace = get_or_update_var(var, None, False)
    is_nonempty(to_replace)
    if to_replace[0] != "string":
        raise_err(OperandsError)

    arg_pos = check_symb_sem(symb1, symb1_type, "int")
    arg_str = check_symb_sem(symb2, symb2_type, "string")

    if 0 > arg_pos or arg_pos >= len(to_replace[1]) or arg_str == "":
        raise_err(StringError)

    arg_str = list(arg_str)

    to_replace[1] = to_replace[1][:arg_pos] + arg_str[0] + to_replace[1][arg_pos + 1:]
    return to_replace[1]


def get_val(val):
    """
    :return: actual processed value of val
    """
    text = val[1]
    arg_type = val[0]
    if arg_type == "int":
        return int(text)
    elif arg_type == "bool":
        return True if text == "true" else False
    elif arg_type == "string":
        return process_esc_seq_in_str(text)
    elif arg_type == "nil":
        return text
    else:
        raise_err(OperandsError)


def compare_values(i_opcode, arg2, arg2_type, arg3, arg3_type):
    """
    prepares two arguments for comparison depending on how
    they are supposed to be evaluated and compares their values

    :return: comparison of values depending on OPCODE
    """
    if arg2_type == "var":
        val1 = get_or_update_var(arg2, None, False)
    else:
        val1 = [arg2.get("type"), arg2.text]
    if arg3_type == "var":
        val2 = get_or_update_var(arg3, None, False)
    else:
        val2 = [arg3.get("type"), arg3.text]
    if val1[0] not in var_types or val2[0] not in var_types:
        raise_err(MissingValError)
    if val1[0] != "nil" and val2[0] != "nil" and arg2_type != "nil" and arg3_type != "nil":
        if arg2_type != arg3_type and val1[0] != val2[0]:
            raise_err(OperandsError)

    cmp1 = get_val(val1)
    cmp2 = get_val(val2)

    if i_opcode in ["EQ", "JUMPIFEQ", "JUMPIFNEQ"]:
        if cmp1 is not None and cmp2 is not None:
            return cmp1 == cmp2
    if cmp1 == "nil" or cmp2 == "nil":
        raise_err(OperandsError)
    elif i_opcode == "LT":
        return cmp1 < cmp2
    elif i_opcode == "GT":
        return cmp1 > cmp2


def jump_if_eq_neq_eval(i_opcode, iip, i_label, symb1, symb1_type, symb2, symb2_type, eq_flag):
    """
    evaluates conditional jumps JUMPIFEQ, JUMPIFNEQ

    :param i_opcode: instruction opcode
    :param iip: internal instruction pointer
    :param i_label: label to jump to
    :param symb1: operator 1 to compare
    :param symb1_type: type of op1
    :param symb2: operator 2 to compare
    :param symb2_type: type of op2
    :param eq_flag: differentiates between jump if EQ and NOT EQ
    :return: evaluation result
    """
    global LD
    if i_label.text not in LD:
        raise_err(SemanticsError)
    eq = compare_values(i_opcode, symb1, symb1_type, symb2, symb2_type)
    if eq_flag:
        if eq:
            return int(LD.get(i_label.text)) - 1
    else:
        if not eq:
            return int(LD.get(i_label.text)) - 1
    return iip


def three_arg_instructions_eval(instr, i_opcode, iip):
    """
    processes instructions that have three arguments

    :param instr: current instruction
    :param i_opcode: instruction opcode
    :param iip: internal instruction pointer
    :return: None on failure
    """
    arg1 = instr[0]
    arg2 = instr[1]
    arg2_type = arg2.get("type")
    arg3 = instr[2]
    arg3_type = arg3.get("type")
    if i_opcode in ["ADD", "SUB", "MUL", "IDIV", "LT", "GT", "EQ", "AND", "OR", "STRI2INT", "CONCAT", "GETCHAR"]:
        check_is_var_defined(arg1)
    if i_opcode in ["ADD", "SUB", "MUL", "IDIV"]:
        num = arithmetic_operations_eval(i_opcode, arg2, arg2_type, arg3, arg3_type)
        val = ["int", num]
        get_or_update_var(arg1, val, True)
    elif i_opcode in ["LT", "GT", "EQ"]:
        comparison = compare_values(i_opcode, arg2, arg2_type, arg3, arg3_type)
        if not comparison:
            comp_str = "false"
        else:
            comp_str = "true"
        val = ["bool", comp_str]
        get_or_update_var(arg1, val, True)
    elif i_opcode in ["AND", "OR"]:
        bool_val = bool_operations_eval(i_opcode, arg2, arg2_type, arg3, arg3_type)
        val = ["bool", bool_val]
        get_or_update_var(arg1, val, True)
    elif i_opcode == "STRI2INT":
        str_char = get_char_in_string_on_pos(arg2, arg2_type, arg3, arg3_type)
        val = ["int", ord(str_char)]
        get_or_update_var(arg1, val, True)
    elif i_opcode == "CONCAT":
        s = concat_eval(arg2, arg2_type, arg3, arg3_type)
        val = ["string", s]
        get_or_update_var(arg1, val, True)
    elif i_opcode == "GETCHAR":
        str_char = get_char_in_string_on_pos(arg2, arg2_type, arg3, arg3_type)
        val = ["string", str_char]
        get_or_update_var(arg1, val, True)
    elif i_opcode == "SETCHAR":
        replaced = set_char_eval(arg1, arg2, arg2_type, arg3, arg3_type)
        val = ["string", replaced]
        get_or_update_var(arg1, val, True)
    elif i_opcode == "JUMPIFEQ":
        iip = jump_if_eq_neq_eval(i_opcode, iip, arg1, arg2, arg2_type, arg3, arg3_type, True)
    elif i_opcode == "JUMPIFNEQ":
        iip = jump_if_eq_neq_eval(i_opcode, iip, arg1, arg2, arg2_type, arg3, arg3_type, False)
    else:
        return None
    return iip


def count_instr(root):
    count = 0
    for _ in root:
        count += 1
    return count


def eval_instructions(root, input_file):
    """
    evaluate all instructions in program (root)

    :param root: main program composed of instructions
    :param input_file: input file
    """
    executed_i = -1  # number of executed instructions
    iip = 0  # internal instruction pointer
    count = count_instr(root)
    while iip < count:
        executed_i += 1
        instr = root[iip]
        i_opcode = instr.get("opcode").upper()
        if i_opcode in zero_arg_instr_list:
            iip = zero_arg_instructions_eval(i_opcode, iip, executed_i)
        elif i_opcode in one_arg_instr_list:
            iip = one_arg_instructions_eval(instr, i_opcode, iip)
        elif i_opcode in two_arg_instr_list:
            iip = two_arg_instructions_eval(instr, i_opcode, iip, input_file)
        elif i_opcode in three_arg_instr_list:
            iip = three_arg_instructions_eval(instr, i_opcode, iip)
        else:
            raise_err(SemanticsError)
        if iip is None:
            raise_err(SemanticsError)
        iip += 1


def sort_root(root):
    """
    sorts instructions in program (root)

    :param root: main program composed of instructions
    :return: sorted root
    """
    has_vals = []
    for i in root:
        if type(i.get("order")) != str:
            raise_err(UnexpectedXMLStructure)
        if not (i.get("order").isdigit()):
            raise_err(UnexpectedXMLStructure)
        if int(i.get("order")) in has_vals or 0 in has_vals:
            raise_err(UnexpectedXMLStructure)
        has_vals.append(int(i.get("order")))
    root[:] = sorted(root, key=lambda child: (child.tag, int(child.get('order'))))
    # sorts arguments of instructions
    for root_child in root:
        root_child[:] = sorted(root_child, key=lambda x: x.tag)
    return root


def check_arg_sem(arg, type_to_check):
    """
    checks semantics of an argument

    :param arg: argument to check value in
    :param type_to_check: user-defined type to check
    """
    arg_type = arg.get("type")
    symb = var_types + ["var"]
    if type_to_check == "symb":
        if arg_type not in symb:
            raise_err(XMLFormatError)
    else:
        if arg_type != type_to_check:
            raise_err(XMLFormatError)


def semantics_check(root):
    """
    checks correctness of semantics in program (root)

    :param root: main program composed of instructions
    """
    for instr in root:
        i_opcode = instr.get("opcode")
        if i_opcode is None:
            raise_err(UnexpectedXMLStructure)
        i_opcode = i_opcode.upper()
        var_fst_arg = ["MOVE", "DEFVAR", "POPS", "ADD", "SUB", "MUL", "IDIV", "LT", "GT", "EQ", "AND", "OR", "NOT",
                       "INT2CHAR", "STRI2INT", "READ", "CONCAT", "STRLEN", "GETCHAR", "SETCHAR", "TYPE"]
        label_fst_arg = ["CALL", "LABEL", "JUMP", "JUMPIFEQ", "JUMPIFNEQ"]
        symb_fst_arg = ["WRITE", "EXIT", "DPRINT"]
        not_symb_snd_arg = zero_arg_instr_list + one_arg_instr_list + ["READ"]
        if i_opcode in var_fst_arg + label_fst_arg + symb_fst_arg:
            if len(instr) < 1:
                raise_err(UnexpectedXMLStructure)
        if i_opcode in var_fst_arg:
            check_arg_sem(instr[0], "var")
        elif i_opcode in label_fst_arg:
            check_arg_sem(instr[0], "label")
        elif i_opcode in symb_fst_arg:
            check_arg_sem(instr[0], "symb")
        if i_opcode not in not_symb_snd_arg:
            if len(instr) < 2:
                raise_err(UnexpectedXMLStructure)
            check_arg_sem(instr[1], "symb")
        if i_opcode in three_arg_instr_list:
            if len(instr) < 3:
                raise_err(UnexpectedXMLStructure)
            check_arg_sem(instr[2], "symb")


def run():
    """
    checks semantics of input XML structure and executes
    program instructions in correct order
    """
    src, inp = handle_args()
    tree = Xml.parse(src)
    root = tree.getroot()
    root = sort_root(root)

    input_file = None
    if inp is not None:
        input_file = open(inp, "r")

    semantics_check(root)
    fill_label_dict_with_labels(root)
    check_root_attrib(root)
    check_instr_xml(root)
    eval_instructions(root, input_file)

    if input_file is not None:
        input_file.close()


def catch_exceptions_and_launch():
    """
    runs the program and catches any error exceptions along the way
    """
    try:
        run()
    except SemanticsError as e:
        exit_err(SemanticsError, e.args[0])
    except Xml.ParseError as e:
        exit_err(XMLFormatError, e.args[0])
    except XMLFormatError as e:
        exit_err(XMLFormatError, e.args[0])
    except MissingValError as e:
        exit_err(MissingValError, e)
    except ParamsError as e:
        exit_err(ParamsError, e.args[0])
    except UnexpectedXMLStructure as e:
        exit_err(UnexpectedXMLStructure, e.args[0])
    except FileNotFoundError as e:
        exit_err(FileNotFoundError, e.args[0])
    except OperandsError as e:
        exit_err(OperandsError, e.args[0])
    except NonexistentFrameError as e:
        exit_err(NonexistentFrameError, e.args[0])
    except NonexistentVarError as e:
        exit_err(NonexistentVarError, e.args[0])
    except OperandValError as e:
        exit_err(OperandValError, e.args[0])
    except StringError as e:
        exit_err(StringError, e.args[0])


catch_exceptions_and_launch()
