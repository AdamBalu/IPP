#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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


def raise_err(err):
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
    print(""
          "Hi my guys, this is help for you!! Haha I think we will be "
          "having so much fun with this project!")


def composed_of_whitespace(x):
    if x is not None:
        if re.search("\S+", x):
            return False
    return True


def process_esc_seq_in_str(string):
    if not string:
        return ""
    for i in range(0, 999):
        string = string.replace("\\{:03}".format(i), chr(i))
    return string


def check_root_attrib(root):
    """
    :param root: xml tree root
    :return: 0 if XML structure is correct, 1 if incorrect
    """
    root_size = len(root.attrib)
    if 1 > root_size > 3:
        return False
    if not composed_of_whitespace(root.text):
        return False
    # check if root has an attribute "language" and if it has more attributes, they are "name" or "description"
    if "language" not in root.attrib or root.get("language").upper() != "IPPCODE22" or \
            (root_size == 2 and ("name" not in root.attrib and "description" not in root.attrib)) or \
            (root_size == 3 and ("name" not in root.attrib or "description" not in root.attrib)):
        return False
    return True


def check_args(instr):
    argc = len(list(instr))
    arg_list = ["arg1", "arg2", "arg3"]
    for i in range(argc):
        curr_arg = instr[i]
        if curr_arg.tag != arg_list[i]:
            return False
        if not composed_of_whitespace(curr_arg.tail):
            return False
        if "type" not in curr_arg.attrib or len(curr_arg.attrib) != 1 or len(curr_arg) != 0:
            return False
    return True


def check_instr_arg_count(instr):
    instr_opcode = instr.attrib.get("opcode").upper()
    instr_arg_count = len(list(instr))
    if instr_opcode in zero_arg_instr_list:
        if instr_arg_count != 0:
            return False
    elif instr_opcode in one_arg_instr_list:
        if instr_arg_count != 1 or not check_args(instr):
            return False
    elif instr_opcode in two_arg_instr_list:
        if instr_arg_count != 2 or not check_args(instr):
            return False
    elif instr_opcode in three_arg_instr_list:
        if instr_arg_count != 3 or not check_args(instr):
            return False
    return True


def check_instructions(root):
    for instr in root:
        if not composed_of_whitespace(instr.text):
            return False
        if not composed_of_whitespace(instr.tail):
            return False
        if instr.tag != "instruction":
            return False
        if not check_instr_arg_count(instr):
            return False
    return True


def check_xml_format(root):
    if root.tag != 'program':
        raise_err(UnexpectedXMLStructure)
    if not check_root_attrib(root):
        raise_err(UnexpectedXMLStructure)
    if not check_instructions(root):
        raise_err(UnexpectedXMLStructure)


def check_symb_sem(arg, arg_type, type_to_check):
    if (arg_type != type_to_check) and (arg_type != "var"):
        raise_err(OperandsError)
    if arg_type == "var":
        var = get_or_update_var(arg, None, False)
        if var[0] not in ["int", "string", "bool", "nil"]:
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
    global LD
    count = 0
    for instr in root:
        opcode = instr.get("opcode").upper()
        if opcode == "LABEL":
            arg = instr[0]
            if arg.text in LD:  # label is already defined
                return False
            LD[arg.text] = count  # add {"label": count} into label dict
        count += 1
    return True


def print_interpret_status(iip, executed_i):
    global GF, LF, TF, FS, CS, DS
    print(
        """
Position in code: {0}

Number of executed instructions: {1}

Global Frame
{2}

Local Frame
{3}

Temporary Frame
{4}

Frame Stack
{5}

Call Stack
{6}

Data Stack
{7}

""".format(iip, executed_i, GF, LF, TF, FS, CS, DS, file=sys.stderr)
    )


def value_check(frame, var, in_frame):
    if (frame is None) and (frame != GF):
        raise_err(NonexistentFrameError)
    if in_frame:
        if var in frame:
            raise_err(SemanticsError)
    else:
        if var not in frame:
            raise_err(NonexistentVarError)


def define_var(arg):
    global LF, TF, GF, FS, CS, DS
    frame = arg.text.split("@")[0]
    var = arg.text.split("@")[1]
    if frame == "LF":
        value_check(LF, var, True)
        LF[var] = ["", ""]
    elif frame == "TF":
        value_check(TF, var, True)
        TF[var] = ["", ""]
    elif frame == "GF":
        value_check(GF, var, True)
        GF[var] = ["", ""]


def check_is_var_defined(arg):
    global LF, TF, GF, FS, CS, DS
    frame = arg.text.split("@")[0]
    var = arg.text.split("@")[1]
    if frame == "LF":
        value_check(LF, var, False)
    elif frame == "TF":
        value_check(TF, var, False)
    elif frame == "GF":
        value_check(GF, var, False)


def get_or_update_var(arg, val, to_update):
    global DS, GF, LF, TF
    frame = arg.text.split("@")[0]
    var = arg.text.split("@")[1]

    if frame == "LF":
        value_check(LF, var, False)
        if to_update:
            LF[var] = [val[0], val[1]]
        else:
            val = LF.get(var)
    elif frame == "TF":
        value_check(TF, var, False)
        if to_update:
            TF[var] = [val[0], val[1]]
        else:
            val = TF.get(var)
    elif frame == "GF":
        value_check(GF, var, False)
        if to_update:
            GF[var] = [val[0], val[1]]
        else:
            val = GF.get(var)
    else:
        return False
    if not to_update:
        return val


def write_var(arg, arg_type, write_on_err):
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
    global TF, FS, CS, LF
    if i_opcode == "CREATEFRAME":
        TF = {}
    elif i_opcode == "PUSHFRAME":
        if TF is None:
            raise_err(NonexistentFrameError)
        FS.append(LF)
        if TF is not None:
            LF = dict(TF.copy())
        TF = None
    elif i_opcode == "POPFRAME":
        if not LF:
            raise_err(NonexistentFrameError)
        TF = LF.copy()
        LF = FS.pop()
    elif i_opcode == "RETURN":
        if not CS:
            raise_err(MissingValError)
        iip = int(CS.pop())
    elif i_opcode == "BREAK":
        print_interpret_status(iip, executed_i)
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
    global GF, TF, LF, FS, CS, DS, LD
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


def read(arg1, arg2, input_file):
    if input_file is None:
        user_input = input()
    else:
        user_input = input_file.readline()
        user_input = "nil" if user_input == '' else user_input.strip()
        
    arg2_type = arg2.text
    if user_input == "nil":
        pass
    elif arg2_type == "int":
        user_input = int(user_input) if re.search("^[+-]?[0-9]*$", user_input) else "nil"
    elif arg2_type == "bool":
        user_input = "true" if re.search("^true$", user_input, flags=re.I) else "false"
    elif arg2_type == "string":
        pass
    elif arg2_type == "nil":
        user_input = "nil"
    else:
        raise_err(SemanticsError)
    to_make = arg2.text if user_input != "nil" else "nil"
    get_or_update_var(arg1, [to_make, user_input], True)


def type_eval(arg1, arg2, arg2_type):
    if arg2_type == "var":
        var_type = get_or_update_var(arg2, None, False)[0]
    else:
        var_type = arg2_type
    var = ["string", var_type]
    get_or_update_var(arg1, var, True)


def not_eval(arg1, arg2, arg2_type):
    val = []
    if arg2_type == "var":
        val = get_or_update_var(arg2, None, False)
        is_nonempty(val)
        if val[0] != "bool":
            raise_err(OperandsError)
    elif arg2_type == "bool":
        val = [arg2_type, arg2.text]
    else:
        raise_err(OperandsError)
    if val[1] == "true":
        val[1] = "false"
    else:
        val[1] = "true"
    get_or_update_var(arg1, val, True)


def int_to_char_eval(arg1, arg2, arg2_type):
    int_val = check_symb_sem(arg2, arg2_type, "int")
    if not (0 < int_val < 1141):
        raise_err(StringError)
    get_or_update_var(arg1, ["string", chr(int_val)], True)


def is_nonempty(val):
    if val[0] not in ["int", "string", "bool", "nil"]:
        raise_err(MissingValError)


def two_arg_instructions_eval(instr, i_opcode, iip, input_file):
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


def arithmetic_operations_eval(i_opcode, arg2, arg2_type, arg3, arg3_type):
    result = None
    n1 = check_symb_sem(arg2, arg2_type, "int")
    n2 = check_symb_sem(arg3, arg3_type, "int")
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


def bool_operations_eval(i_opcode, arg2, arg2_type, arg3, arg3_type):
    b1 = check_symb_sem(arg2, arg2_type, "bool")
    b2 = check_symb_sem(arg3, arg3_type, "bool")
    result = None
    if i_opcode == "AND":
        result = "true" if b1 == "true" and b2 == "true" else "false"
    elif i_opcode == "OR":
        result = "true" if b1 == "true" or b2 == "true" else "false"
    return result


def get_char_in_string_on_pos(arg2, arg2_type, arg3, arg3_type):
    arg_str = check_symb_sem(arg2, arg2_type, "string")
    arg_pos = check_symb_sem(arg3, arg3_type, "int")
    if 0 > arg_pos or arg_pos >= len(arg_str):
        raise_err(StringError)
    return arg_str[arg_pos]


def concat_eval(arg2, arg2_type, arg3, arg3_type):
    s1 = check_symb_sem(arg2, arg2_type, "string")
    s2 = check_symb_sem(arg3, arg3_type, "string")
    if s1 is None or s2 is None:
        return ""
    s = s1 + s2
    return s


def set_char_eval(arg1, arg2, arg2_type, arg3, arg3_type):
    to_replace = get_or_update_var(arg1, None, False)
    is_nonempty(to_replace)
    if to_replace[0] != "string":
        raise_err(OperandsError)

    arg_pos = check_symb_sem(arg2, arg2_type, "int")
    arg_str = check_symb_sem(arg3, arg3_type, "string")

    if 0 > arg_pos or arg_pos >= len(to_replace[1]) or arg_str == "":
        raise_err(StringError)

    arg_str = list(arg_str)

    to_replace[1] = to_replace[1][:arg_pos] + arg_str[0] + to_replace[1][arg_pos + 1:]
    return to_replace[1]


def get_val(val):
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
    if arg2_type == "var":
        val1 = get_or_update_var(arg2, None, False)
    else:
        val1 = [arg2.get("type"), arg2.text]
    if arg3_type == "var":
        val2 = get_or_update_var(arg3, None, False)
    else:
        val2 = [arg3.get("type"), arg3.text]
    if val1[0] not in ["int", "string", "bool", "nil"] or val2[0] not in ["int", "string", "bool", "nil"]:
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


def jump_iq_eq_neq_eval(i_opcode, iip, arg1, arg2, arg2_type, arg3, arg3_type, eq_flag):
    global LD
    if arg1.text not in LD:
        raise_err(SemanticsError)
    eq = compare_values(i_opcode, arg2, arg2_type, arg3, arg3_type)
    if eq_flag:
        if eq:
            return int(LD.get(arg1.text)) - 1
    else:
        if not eq:
            return int(LD.get(arg1.text)) - 1
    return iip


def three_arg_instructions_eval(instr, i_opcode, iip):
    global GF, TF, LF, FS, CS, LD
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
        iip = jump_iq_eq_neq_eval(i_opcode, iip, arg1, arg2, arg2_type, arg3, arg3_type, True)
    elif i_opcode == "JUMPIFNEQ":
        iip = jump_iq_eq_neq_eval(i_opcode, iip, arg1, arg2, arg2_type, arg3, arg3_type, False)
    else:
        return None
    return iip


def count_instr(root):
    count = 0
    for _ in root:
        count += 1
    return count


def eval_instructions(root, input_file):
    global GF, TF, LF, FS, CS
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
            return False
        if iip is None:
            return False
        iip += 1
    # TODO file exists check
    return True


def sort_root(root):
    # sorts instructions
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


def check_instr_sem(arg, type_to_check):
    arg_type = arg.get("type")
    symb = ["int", "bool", "string", "nil", "var"]
    if type_to_check == "symb":
        if arg_type not in symb:
            raise_err(XMLFormatError)
    else:
        if arg_type != type_to_check:
            raise_err(XMLFormatError)


def semantics_check(root):
    for instr in root:
        i_opcode = instr.get("opcode")
        if i_opcode is not None:
            i_opcode = i_opcode.upper()
        else:
            raise_err(UnexpectedXMLStructure)

        var_fst_arg = ["MOVE", "DEFVAR", "POPS", "ADD", "SUB", "MUL", "IDIV", "LT", "GT", "EQ", "AND", "OR", "NOT",
                       "INT2CHAR", "STRI2INT", "READ", "CONCAT", "STRLEN", "GETCHAR", "SETCHAR", "TYPE"]
        label_fst_arg = ["CALL", "LABEL", "JUMP", "JUMPIFEQ", "JUMPIFNEQ"]
        symb_fst_arg = ["WRITE", "EXIT", "DPRINT"]
        not_symb_snd_arg = zero_arg_instr_list + one_arg_instr_list + ["READ"]
        if i_opcode in var_fst_arg + label_fst_arg + symb_fst_arg:
            if len(instr) < 1:
                raise_err(UnexpectedXMLStructure)
        if i_opcode in var_fst_arg:
            check_instr_sem(instr[0], "var")
        elif i_opcode in label_fst_arg:
            check_instr_sem(instr[0], "label")
        elif i_opcode in symb_fst_arg:
            check_instr_sem(instr[0], "symb")
        if i_opcode not in not_symb_snd_arg:
            if len(instr) < 2:
                raise_err(UnexpectedXMLStructure)
            check_instr_sem(instr[1], "symb")
        if i_opcode in three_arg_instr_list:
            if len(instr) < 3:
                raise_err(UnexpectedXMLStructure)
            check_instr_sem(instr[2], "symb")


def run():
    src, inp = handle_args()
    tree = Xml.parse(src)
    root = tree.getroot()
    root = sort_root(root)

    input_file = None
    if inp is not None:
        input_file = open(inp, "r")

    semantics_check(root)
    fld_error_check = fill_label_dict_with_labels(root)
    if not fld_error_check:
        raise_err(SemanticsError)

    check_xml_format(root)

    eval_error_check = eval_instructions(root, input_file)
    if not eval_error_check:
        raise_err(SemanticsError)

    if input_file is not None:
        input_file.close()


def catch_exceptions_and_launch():
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
