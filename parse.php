<?php
$regex_var = "/^(LF|TF|GF)@([a-zA-Z\_\-$&%\*!\?])([\w\-$&%\*!\?])*$/";
$regex_label = "/^([a-zA-Z\_\-$&%\*!\?])([\w\-$&%\*!\?])*$/";
$regex_const = "/^(int|bool|string|nil)@(\\\\[0-9]{3}|[!-~]|[§áčďéěíňóřšťúůýž])*$/u";
$regex_type = "/^(int|bool|string|nil)$/";

$instruction_count = 0;

// BONUS EXPANSION class
class Stats {
    public $loc = 0;
    public $comments = 0;
    public $labels = 0;
    public $jumps = 0;
    public $fwjumps = 0;
    public $backjumps = 0;
    public $badjumps = 0;
    public $label_arr = array();
    public $forward_labels_arr = array();
}

$stats = new Stats();

$xml = new DomDocument("1.0", "UTF-8");
$xml->formatOutput = true;

$root = $xml->createElement("program");
$xml->appendChild($root);
$root->setAttribute("language", "IPPcode22");
$instruction = NULL;

if (!defined('STDIN')) { define('STDIN', fopen('php://stdin', 'r')); }
if (!defined('STDERR')) { define('STDERR', fopen('php://stderr', "w")); }
const ERR_PARAM = 10;
const ERR_FILE_OPEN = 12;
const ERR_HEADER = 21;
const ERR_OPCODE = 22;
const ERR_LEX_OTHER = 23;
const CODE_SUCCESS = 0;

function print_help() {
    echo
"Script receives source code written in IPPCode22 from standard input, checks lexical and
syntactic correctness and prints XML representation of the program on standard output.

USAGE: php8.1 parse.php [--help] [--stats=FILE STAT]
--help
        display this help and exit
--stats=FILE
    prints program statistics into a given FILE. In case of multiple --stats paremetres,
    statistics following this parameter are written into most recently defined file.
STAT can be one (or more) of the following, separated by whitespace:
--loc
    prints number of lines of undead code
--comments
    prints number of comments
--labels
    prints number of labels
--jumps
    prints number of jumps in total
--fwjumps
    prints number of forward jumps
--backjumps
    prints number of backward jumps
--badjumps
    prints number of wrong jumps which are not defined by a label
        \n";
}

function error_handle($err_num) {
    fwrite(STDERR, "Error $err_num" . PHP_EOL);
    exit($err_num);
}

function arg_check() {
    global $argc, $argv;
    for ($i = 1; $i < $argc; $i++) {
        $arg = $argv[$i];
        if (preg_match("/^--stats=/", $arg)) { $arg = "--stats"; }
        switch ($arg) {
            case "--help":
                if ($argc == 2) {
                    print_help();
                    exit(CODE_SUCCESS);
                }
                else {
                    error_handle(ERR_PARAM);
                }
                break;
            case "--stats":
            case "--loc":
            case "--comments":
            case "--labels":
            case "--jumps":
            case "--fwjumps":
            case "--backjumps":
            case "--badjumps":
                break;
            default:
                error_handle(ERR_PARAM);

        }
    }
}

function check_const_syntax($arg) {
    // types of constants - syntax checking
    if      (preg_match("/^int@[\-|\+]?[0-9]+$/", $arg) === 1) { return "int"; }
    else if (preg_match("/^nil@nil$/", $arg)            === 1) { return "nil"; }
    else if (preg_match("/^bool@(true|false)$/", $arg)  === 1) { return "bool"; }
    else if (preg_match("/^string@(\\\\[0-9]{3}|[$-\[]|[\]-~]|[!\"§áčďéěíňóřšťúůýž])*$/", $arg) ) { return "string"; }
    else { error_handle(ERR_LEX_OTHER); }
}

function create_xml_instruction($cmd) {
    GLOBAL $xml, $instruction_count, $root, $stats;
    $i = $xml->createElement("instruction");
    $root->appendChild($i);
    $i->setAttribute("order", $instruction_count);
    $i->setAttribute("opcode", $cmd);

    // every line of code creates xml instruction
    $stats->loc++;
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
 * saves to xml if lex and syntax are both coorect
 * 
 * @param args instruction arguments
 * @param cmd instruction command
 */
function choose_by_args($args, $cmd) {
    GLOBAL $instruction_count, $instruction, $stats;
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
            if ($cmd == "RETURN") { $stats->jumps++; }
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
        case "LABEL":
            if ($arg_num != 1) { error_handle(ERR_LEX_OTHER); }
            if (!in_array($args[1], $stats->label_arr)) {
                array_push($stats->label_arr, $args[1]);
                $stats->labels++;
            }
        case "CALL":
        case "JUMP":
            $arg1_type = "label";
            if ($arg_num != 1) { error_handle(ERR_LEX_OTHER); }
            $instruction = create_xml_instruction($cmd);
            one_arg_label($args[1]);
            if ($cmd == "CALL" || $cmd == "JUMP") {
                $stats->jumps++;
                if (in_array($args[1], $stats->label_arr)) { $stats->backjumps++; }
                else { array_push($stats->forward_labels_arr, $args[1]); }
            }
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
            $stats->jumps++;
            $instruction = create_xml_instruction($cmd);
            three_arg_label_symb_symb($args[1], $args[2], $args[3], $arg2_type, $arg3_type);

            if (in_array($args[1], $stats->label_arr)) { $stats->backjumps++; }
            else { array_push($stats->forward_labels_arr, $args[1]); }

            add_xml_arg($instruction, $args[1], $args[2], $args[3], $arg1_type, $arg2_type, $arg3_type);
            break;
        default:
            error_handle(ERR_OPCODE);
            break;
    }
}

/**
 * splits line into instruction and arguments with whitespace as a delimiter
 * and sends them for further processing
 */
function split_line($str) {
    $parsed_str = preg_split("/\s+/", $str);
    $cmd_to_pass = strtoupper($parsed_str[0]);
    choose_by_args($parsed_str, $cmd_to_pass);
}

/**
 * all of the match functions check if the code is correct from lexical and syntactic standpoint,
 * for 'symbol' type they find out which type they are (it can be a variable, int, string etc.)
 * @return arg_type type of argument in case of a constant, otherwise no value is returned
 */
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

/**
 * every command falls into one of these following types
 * depending on it's argument count
 * these functions send arguments for lexical and syntactic correctness checking
 */
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

/**
 * counts forward jumps and bad jumps by checking forward_labels_arr array
 */
function check_forward_labels() {
    GLOBAL $stats;
    foreach ($stats->forward_labels_arr as &$label_to_check) {
        if (in_array($label_to_check, $stats->label_arr)) { $stats->fwjumps++; }
        else { $stats->badjumps++; }
    }
}

/**
 * writes out expansion statistics into a given file (filename after "--stats=")
 */
function print_stats() {
    GLOBAL $stats, $argc, $argv;
    $opened_files = array();
    $file_defined = false;
    for ($i = 1; $i < $argc; $i++) {
        $arg = $argv[$i];
        
        if (preg_match("/^--stats=/", $arg)) {
            $file_name = preg_replace("/^--stats=/", "", $arg);
            if (in_array($file_name, $opened_files)) { error_handle(ERR_FILE_OPEN); }
            array_push($opened_files, $file_name);
            if ($file_name === "") { error_handle(ERR_FILE_OPEN); }
            $arg = "--stats";
        }
        if (!$file_defined && ($arg != "--stats")) { error_handle(ERR_PARAM); }
        switch ($arg) {
            case "--stats":
                $file_defined = true;
                $file = fopen($file_name, "w");
                if ($file === false) { error_handle(ERR_PARAM); };
                break;
            case "--loc":
                fwrite($file, "$stats->loc" . "\n");
                break;
            case "--comments":
                fwrite($file, "$stats->comments" . "\n");
                break;
            case "--labels":
                fwrite($file, "$stats->labels" . "\n");
                break;
            case "--jumps":
                fwrite($file, "$stats->jumps" . "\n");
                break;
            case "--fwjumps":
                fwrite($file, "$stats->fwjumps" . "\n");
                break;
            case "--backjumps":
                fwrite($file, "$stats->backjumps" . "\n");
                break;
            case "--badjumps":
                fwrite($file, "$stats->badjumps" . "\n");
                break;
            default:
                break;
        }
    }


}

function main() {
    GLOBAL $stats;
    ini_set('display_errors', 'stderr');
    
    $ippcodefound = false;
    arg_check();
    while ($line = fgets(STDIN)) {
        if (preg_match("/#/", $line)) { $stats->comments++; }

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
    check_forward_labels();
    print_stats();
}
main();
$xml->save("php://stdout");
exit(CODE_SUCCESS);
?>
