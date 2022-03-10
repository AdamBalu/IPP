<?php
$regex_var = "/^(LF|TF|GF)@([a-zA-Z\_\-$&%\*!\?])([\w\-$&%\*!\?])*$/";
$regex_label = "/^([a-zA-Z\_\-$&%\*!\?])([\w\-$&%\*!\?])*$/";
$regex_const = "/^(int|bool|string|nil)@(\\\\[0-9]{3}|[!-~]|[§áčďéěíňóřšťúůýž])*$/u";
$regex_type = "/^(int|bool|string|nil)$/";

$instruction_count = 0;

$xml = new DomDocument("1.0", "UTF-8");
$xml->formatOutput = true;

$root = $xml->createElement("program");
$xml->appendChild($root);
$root->setAttribute("language", "IPPcode22");
$instruction = NULL;

if (!defined('STDIN')) { define('STDIN', fopen('php://stdin', 'r')); }
if (!defined('STDERR')) { define('STDERR', fopen('php://stderr', "w")); }
const ERR_PARAM = 10;
const ERR_HEADER = 21;
const ERR_OPCODE = 22;
const ERR_LEX_OTHER = 23;
const CODE_SUCCESS = 0;

function print_help() {
    echo
"Script receives source code written in IPPCode22 from standard input, checks lexical and
syntactic correctness and prints XML representation of the program on standard output.

USAGE: php8.1 parse.php [--help]
--help
        display this help and exit\n";
}

function error_handle($err_num) {
    fwrite(STDERR, "Error $err_num" . PHP_EOL);
    exit($err_num);
}

function parse_args() {
    global $argc, $argv;
    if ($argc > 2) { error_handle(ERR_PARAM); }
    else {
        if ($argc > 1) {
            if ($argv[1] == "--help") {
                print_help();
                exit(CODE_SUCCESS);
            }
            else {
                error_handle(ERR_PARAM);
            }
        }
        
    }
}

function check_const_syntax($arg) {
    // types of constants - syntax checking
    if      (preg_match("/^int@[\-|\+]?[0-9]+$/", $arg) === 1) { return "int"; }
    else if (preg_match("/^nil@nil$/", $arg)              === 1) { return "nil"; }
    else if (preg_match("/^bool@(true|false)$/", $arg)    === 1) { return "bool"; }
    else if (preg_match("/^string@(\\\\[0-9]{3}|[!-\[]|[\]-~]|[§áčďéěíňóřšťúůýž])*$/", $arg) ) { return "string"; }
    else { error_handle(ERR_LEX_OTHER); }
}

function create_xml_instruction($cmd) {
    GLOBAL $xml, $instruction_count, $root;
    $i = $xml->createElement("instruction");
    $root->appendChild($i);
    $i->setAttribute("order", $instruction_count);
    $i->setAttribute("opcode", $cmd);
    return $i;
}

function remove_prefix($arg, $arg_type) {
    $out_str = $arg;
    switch ($arg_type) {
        case "var":
        case "type":
        case "label":
            break;
        case "int":
        case "bool":
        case "string":
        case "nil":
            $out_str = preg_replace("/^.*@/", "", $arg);
            break;
        default:
            break;
    }
    return $out_str;
}

/**
 * appends instruction arguments to xml output
 */
function add_xml_arg($instr, $arg1, $arg2, $arg3, $arg1_type, $arg2_type, $arg3_type) {
    GLOBAL $xml;
    if ($arg1 !== "") {
        $val = remove_prefix($arg1, $arg1_type);
        $arg1_xml = $xml->createElement("arg1", htmlspecialchars($val));
        $instr->appendChild($arg1_xml);
        $arg1_xml->setAttribute("type", $arg1_type);
    }
    if ($arg2 !== "") {
        $val = remove_prefix($arg2, $arg2_type);
        $arg2_xml = $xml->createElement("arg2", htmlspecialchars($val));
        $instr->appendChild($arg2_xml);
        $arg2_xml->setAttribute("type", $arg2_type);
    }
    if ($arg3 !== "") {
        $val = remove_prefix($arg3, $arg3_type);
        $arg3_xml = $xml->createElement("arg3", htmlspecialchars($val));
        $instr->appendChild($arg3_xml);
        $arg3_xml->setAttribute("type", $arg3_type);
    }
}

/**
 * decides how to parse arguments depending on their type 
 * (instructions have common and repeating parameter patterns)
 * 
 * @param args instruction arguments
 * @param cmd instruction command
 */
function choose_by_args($args, $cmd) {
    GLOBAL $instruction_count, $instruction;
    $arg1_type = "";
    $arg2_type = "";
    $arg3_type = "";
    $instruction_count++;
    $arg_num = count($args) - 1;
    switch($cmd) {
        case "CREATEFRAME":
        case "PUSHFRAME":
        case "POPFRAME":
        case "RETURN":
        case "BREAK":
            if ($arg_num > 0) { error_handle(ERR_LEX_OTHER); }
            $instruction = create_xml_instruction($cmd);
            break;
        case "DEFVAR":
        case "POPS":
            $arg1_type = "var";
            if ($arg_num != 1) { error_handle(ERR_LEX_OTHER); }
            one_arg_var($args[1]);
            $instruction = create_xml_instruction($cmd);
            add_xml_arg($instruction, $args[1], "", "", $arg1_type, $arg2_type, $arg3_type);
            break;
        case "CALL":
        case "LABEL":
        case "JUMP":
            $arg1_type = "label";
            if ($arg_num != 1) { error_handle(ERR_LEX_OTHER); }
            $instruction = create_xml_instruction($cmd);
            one_arg_label($args[1]);
            add_xml_arg($instruction, $args[1], "", "", $arg1_type, $arg2_type, $arg3_type);
            break;
        case "PUSHS":
        case "WRITE":
        case "EXIT":
        case "DPRINT":
            if ($arg_num != 1) { error_handle(ERR_LEX_OTHER); }
            $instruction = create_xml_instruction($cmd);
            one_arg_symb($args[1], $arg1_type);
            add_xml_arg($instruction, $args[1], "", "", $arg1_type, $arg2_type, $arg3_type);
            break;
        case "MOVE":
        case "INT2CHAR":
        case "STRLEN":
        case "TYPE":
        case "NOT":
            $arg1_type = "var";
            if ($arg_num != 2) { error_handle(ERR_LEX_OTHER); }
            $instruction = create_xml_instruction($cmd);
            two_arg_var_symb($args[1], $args[2], $arg2_type);
            add_xml_arg($instruction, $args[1], $args[2], "", $arg1_type, $arg2_type, $arg3_type);
            break;
        case "READ":
            $arg1_type = "var";
            $arg2_type = "type";
            if ($arg_num != 2) { error_handle(ERR_LEX_OTHER); }
            $instruction = create_xml_instruction($cmd);
            two_arg_var_type($args[1], $args[2]);
            add_xml_arg($instruction, $args[1], $args[2], "", $arg1_type, $arg2_type, $arg3_type);
            break;
        case "ADD":
        case "SUB":
        case "MUL":
        case "IDIV":
        case "LT":
        case "GT":
        case "EQ":
        case "AND":
        case "OR":
        case "CONCAT":
        case "GETCHAR":
        case "SETCHAR":
        case "STRI2INT":
            $arg1_type = "var";
            if ($arg_num != 3) { error_handle(ERR_LEX_OTHER); }
            $instruction = create_xml_instruction($cmd);
            three_arg_var_symb_symb($args[1], $args[2], $args[3], $arg2_type, $arg3_type);
            add_xml_arg($instruction, $args[1], $args[2], $args[3], $arg1_type, $arg2_type, $arg3_type);
            break;
        case "JUMPIFEQ":
        case "JUMPIFNEQ":
            $arg1_type = "label";
            if ($arg_num != 3) { error_handle(ERR_LEX_OTHER); }
            $instruction = create_xml_instruction($cmd);
            three_arg_label_symb_symb($args[1], $args[2], $args[3], $arg2_type, $arg3_type);
            add_xml_arg($instruction, $args[1], $args[2], $args[3], $arg1_type, $arg2_type, $arg3_type);
            break;
        default:
            error_handle(ERR_OPCODE);
            break;
    }
}

/**
 * splits arguments by spaces and sends them for lex/syntax check
 * @param str current line - instruction with arguments (stripped of comments)
 */
function split_line($str) {
    $parsed_str = preg_split("/\s+/", $str);
    $cmd_to_pass = strtoupper($parsed_str[0]);
    choose_by_args($parsed_str, $cmd_to_pass);
}

// match functions check if the code is correct from lexical and syntactic standpoint
// for symbol types they find out which type they are (it can be a variable, int, string etc.)
function match_var($arg) {
    GLOBAL $regex_var;
    if (!(preg_match($regex_var, $arg))) { error_handle(ERR_LEX_OTHER); }
}

function match_symb($arg) {
    GLOBAL $regex_const;
    GLOBAL $regex_var;
    $const_match = preg_match($regex_const, $arg);
    if (!($const_match ||
            preg_match($regex_var, $arg)) ) { error_handle(ERR_LEX_OTHER); }
    if ($const_match) { $arg_type = check_const_syntax($arg); }
    else { $arg_type = "var"; }
    return $arg_type;
}

function match_label($arg) {
    GLOBAL $regex_label;
    if (!(preg_match($regex_label, $arg))) { error_handle(ERR_LEX_OTHER); }
}

function match_type($arg) {
    GLOBAL $regex_type;
    if (!( preg_match($regex_type, $arg))) { error_handle(ERR_LEX_OTHER); }
}

// every command falls into one of these categories
// depending on it's argument counts and types
function one_arg_var($arg) { match_var($arg); }

function one_arg_symb($arg, &$arg1_type) { 
    $arg1_type = match_symb($arg);
}

function one_arg_label($arg) { match_label($arg); }

function two_arg_var_symb($arg1, $arg2, &$arg2_type) {
    match_var($arg1);
    $arg2_type = match_symb($arg2);
}

function two_arg_var_type($arg1, $arg2) {
    match_var($arg1);
    match_type($arg2);
}

function three_arg_var_symb_symb($arg1, $arg2, $arg3, &$arg2_type, &$arg3_type) {
    match_var($arg1);
    $arg2_type = match_symb($arg2);
    $arg3_type = match_symb($arg3);
}

function three_arg_label_symb_symb($arg1, $arg2, $arg3, &$arg2_type, &$arg3_type) {
    match_label($arg1);
    $arg2_type = match_symb($arg2);
    $arg3_type = match_symb($arg3);
}

function main() {
    ini_set('display_errors', 'stderr');
    
    $ippcodefound = false;
    parse_args();
    while ($line = fgets(STDIN)) {
        $out_str = trim(preg_replace("/#.*$/", "", $line));
        // empty line
        if ($out_str === "") { continue; }

        if ($ippcodefound) {
            split_line($out_str);
        }
        else if (strtolower($out_str) == ".ippcode22") {
            $ippcodefound = true;
        }
        else { error_handle(ERR_HEADER); }
    }
}

main();
$xml->save("php://stdout");
exit(CODE_SUCCESS);
?>
