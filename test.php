<?php
############################################
# TESTSUITE FOR PARSE.PHP AND INTERPRET.PY #
# Author: Adam Balušeskul                  #
# login: xbalus01                          #
############################################

class Argtype {
        public bool $help;
        public bool $directory;
        public bool $recursive;
        public bool $parse_script;
        public bool $int_script;
        public bool $parse_only;
        public bool $int_only;
        public bool $jexampath;
        public bool $noclean;
        public string $directory_path;
        public string $jexam_path;
        public string $parse_script_file;
        public string $int_script_file;
    }


    $correct_tests_count = 0;
    $total_tests_count = 0;
    $correct_tests_html = "";
    $incorrect_tests_html = "";
    

    if (!defined('STDERR')) { define('STDERR', fopen('php://stderr', "w")); }

    function error_handle(int $err_num): void
    {
        if ($err_num === 41) {
            $msg = "directory or file doesn't exist\n";
        } else {
            $msg = "$err_num";
        }
        fwrite(STDERR, "Error: $msg" . PHP_EOL);
        exit($err_num);
    }

    function print_help(): void
    {
        echo
"Test suite is used for gradual testing of the applications parse.php and interpret.py

USAGE: php8.1 test.php [OPTION]
--help
        display this help and exit
        
--directory=PATH
looks for tests in given directory (if the parameter is missing, script is going through the current directory)

--recursive
looks for tests not only in given directory, but also recursively in all of its subdirectories

--parse-script=file
file with script in PHP 8.1 for the analysis of source code in IPPcode22
(if this parameter is missing, implicit value is parse.php saved in current working directory)

--int-script=file
file with script in Python 3.8 for interpreter of XML representation written 
in IPPcode22 (if this parameter is missing, implicit value is interpret.py saved in current working directory)

--parse-only
only a script for source code analysis in IPPcode22 will be tested (this parameter must not be combined
with parameters --int-only and --int-script), output is compared using A7Soft JExamXML tool.

--int-only
only a script for an interpreter of an XML representation of a code written in IPPcode22 will be tested
(this parameter must not be combined with parameters --parse-only, --parse-script and --jexampath).
Input program represented using XML will be in a file with .src suffix.

--jexampath=path
path to directory containing file jexamxml.jar with JAR package which includes A7Soft JExamXML tool and a file
with a configuration named options. If this parameter is not included, an implicit location /pub/courses/ipp/jexamxml/
is used.

--noclean
while test.php is running, no files containing helping results will be deleted - script will retain files that
are created during work with testing scripts (e.g. file with produced XML after execution of parse.php etc.).
";}

    function argtype_init(Argtype $argtype): void
    {
        $argtype->help = false;
        $argtype->directory = false;
        $argtype->recursive = false;
        $argtype->parse_script = false;
        $argtype->int_script = false;
        $argtype->parse_only = false;
        $argtype->int_only = false;
        $argtype->jexampath = false;
        $argtype->noclean = false;
        $argtype->directory_path = ".";
        $argtype->jexam_path = "/pub/courses/ipp/jexamxml/";
        $argtype->parse_script_file = "parse.php";
        $argtype->int_script_file = "interpret.py";
    }

    function check_if_files_exist(Argtype $argtype): void
    {
        if (file_exists($argtype->directory_path)    === false ||
            file_exists($argtype->jexam_path)        === false ||
            file_exists($argtype->int_script_file)   === false ||
            file_exists($argtype->parse_script_file) === false) {
            error_handle(41);
        }
    }

    function both($f, Argtype $argtype): void
    {
        GLOBAL $total_tests_count, $correct_tests_count, $correct_tests_html, $incorrect_tests_html;
        if (preg_match("/^.*\.src$/", $f) === 1) {
            $total_tests_count++;
            $parse_path = $argtype->parse_script_file;
            shell_exec('php ' . $parse_path . ' < ' . $f . ' > test.src');
            $f_stripped = preg_replace("/\.src$/", "", $f);
            $input_file = preg_replace("/\.src$/", ".in", $f);
            $output_file = preg_replace("/\.src$/", ".out", $f);
            shell_exec('echo -n >>'. $input_file);
            shell_exec('echo -n >>'. $output_file);
            $wd = getcwd();
            $source_file = "--source=" . $wd . "/test.src";
            $input = "--input=" . $input_file;
            $interpreter_path = $argtype->int_script_file;
            shell_exec('python3.8 '. $interpreter_path . ' ' . $source_file .' '. $input . '> test.out; echo $? > test.rc');
            
            $f_stripped_rc = $f_stripped . ".rc";
            if (file_get_contents($f_stripped_rc) === false) {
                shell_exec('echo -n >>'. $f_stripped_rc . ';echo 0 | tr -d "\n" > ' . $f_stripped_rc);
            }

            $file_o = fopen("test.rc", "r");
            $foo = fgets($file_o, 3);
            exec("diff -qb \"$f_stripped_rc\" \"test.rc\"", $dump, $diff);
            exec("diff -qb \"$output_file\" \"test.out\"", $dump2, $diff2);

            fclose($file_o);
            if ((!$diff && !$diff2) || ($foo !== "0" && !$diff)) {
                $correct_tests_count++;
                $correct_tests_html .= "<tr><td>$f</td></tr>";
            } else {
                $incorrect_tests_html .= "<tr><td>$f</td></tr>";
            }
        }
    }


    function open_file($f, Argtype $argtype): void
    {
        GLOBAL $total_tests_count, $correct_tests_count, $correct_tests_html, $incorrect_tests_html;
        if (preg_match("/^.*\.src$/", $f) === 1) {
            $total_tests_count++;
            $parse_path = $argtype->parse_script_file;
            shell_exec('php ' . $parse_path . ' < ' . $f . ' > test.out; echo $? | tr -d "\n" > test.rc');
            $f_stripped = preg_replace("/\.src$/", "", $f);

            $f_stripped_rc = $f_stripped . ".rc";
            $f_stripped_out = $f_stripped . ".out";
            exec("diff -qb \"$f_stripped_rc\" \"test.rc\"", $dump, $diff);
            if (!$diff) {
                $output = file_get_contents("test.rc");
                if ($output == "0") {
                    $jexam_jar_p = $argtype->jexam_path . "jexamxml.jar";
                    $options_p = $argtype->jexam_path . "options";
                    exec("java -jar $jexam_jar_p test.out $f_stripped_out delta.xml $options_p", $dump, $xml_diff);
                    if ($xml_diff === 0) {
                        $correct_tests_count++;
                        $correct_tests_html .= "<tr><td>$f</td></tr>";
                    } else {
                        $incorrect_tests_html .= "<tr><td>$f</td></tr>";
                    }
                } else {
                    $correct_tests_count++;
                    $correct_tests_html .= "<tr><td>$f</td></tr>";
                }
            }
        }
    }


    function open_file_int($f, $argtype): void
    {
        GLOBAL $total_tests_count, $correct_tests_count, $correct_tests_html, $incorrect_tests_html;
        if (preg_match("/^.*\.src$/", $f) === 1) {
            $total_tests_count++;
            $f_stripped = preg_replace("/\.src$/", "", $f);
            $input_file = preg_replace("/\.src$/", ".in", $f);
            $output_file = preg_replace("/\.src$/", ".out", $f);
            shell_exec('echo -n >>'. $input_file);
            shell_exec('echo -n >>'. $output_file);
            $source_file = "--source=" . $f_stripped . ".src";
            $input = "--input=" . $input_file;
            $interpreter_path = $argtype->int_script_file;
            shell_exec('python3.8 ' . $interpreter_path . ' ' .
                $source_file .' '. $input . '> test.out; echo $? | tr -d "\n" > test.rc');
            
            $f_stripped_rc = $f_stripped . ".rc";
            if (file_get_contents($f_stripped_rc) === false) {
                shell_exec('echo -n >>'. $f_stripped_rc . ';echo 0 | tr -d "\n" > ' . $f_stripped_rc);
            }

            $file_o = fopen("test.rc", "r");
            $foo = fgets($file_o, 3);
            exec("diff -qb \"$f_stripped_rc\" \"test.rc\"", $dump, $diff);
            exec("diff -qb \"$output_file\" \"test.out\"", $dump, $diff2);
            fclose($file_o);
            if (!$diff && !$diff2 || ($foo !== "0" && !$diff)) {
                $correct_tests_count++;
                $correct_tests_html .= "<tr><td>$f</td></tr>";
            } else {
                $incorrect_tests_html .= "<tr><td>$f</td></tr>";
            }
        }
    }

    function run_tests(Argtype $argtype): void
    {
        global $argc;
        if ($argtype->help) {
            if ($argc > 2) { error_handle(10); }
            print_help();
            exit(0);
        }
        check_if_files_exist($argtype);
        // path is not a directory
        if (!is_dir($argtype->directory_path)) { error_handle(41); }

        // recursively go through all files in given folder
        if ($argtype->recursive) {
            $dir_iterator = new RecursiveDirectoryIterator($argtype->directory_path);
            $iterator = new RecursiveIteratorIterator($dir_iterator, RecursiveIteratorIterator::SELF_FIRST);
            foreach ($iterator as $file) {
                if ($file->isFile()) {
                    if ($argtype->int_only !== true && $argtype->parse_only !== true) {
                        both($file, $argtype);
                    }
                    else if ($argtype->int_only !== true) {
                        open_file($file, $argtype);
                    }
                    else if ($argtype->parse_only !== true) {
                        open_file_int($file, $argtype);
                    }
                    else {
                        error_handle(10);
                    }
                }
            }
        }

        // only go through files in given path directory
        else if ($dh = opendir($argtype->directory_path)) {
            while (($file = readdir($dh)) !== false) {
                $full_path = $argtype->directory_path . "/" . $file;
                if ($argtype->int_only !== true && $argtype->parse_only !== true) {
                    both($full_path, $argtype);
                }
                else if ($argtype->int_only !== true) {
                    open_file($full_path, $argtype);
                }
                else if ($argtype->parse_only !== true) {
                    open_file_int($full_path, $argtype);
                }
            }
            closedir($dh);
        }
        else { error_handle(41); }
        
    }

    function add_attrib(&$attr_type): void
    {
        if ($attr_type === true) {
            error_handle(10);
        } else {
            $attr_type = true;
        }
    }

    function parse_args_test(Argtype $argtype) {
        global $argc, $argv;

        // no arguments
        if ($argc < 2) { return 0; }
        
        for ($i = 1; $i < count($argv); $i++) {
            $arg = $argv[$i];
            if (preg_match("/^--help$/", $arg) === 1) {
                add_attrib($argtype->help);
            }
            else if (preg_match("/^--directory=.+$/", $arg) === 1) {
                add_attrib($argtype->directory);
                $argtype->directory_path = preg_replace("/^--directory=/", "", $arg);
            }
            else if (preg_match("/^--recursive$/", $arg) === 1) {
                add_attrib($argtype->recursive);
            }
            else if (preg_match("/^--parse-script=.+$/", $arg) === 1) {
                add_attrib($argtype->parse_script);
                $argtype->parse_script_file = preg_replace("/^--parse-script=/", "", $arg);
            }
            else if (preg_match("/^--int-script=.+$/", $arg) === 1) {
                add_attrib($argtype->int_script);
                $argtype->int_script_file = preg_replace("/^--int-script=/", "", $arg);
            }
            else if (preg_match("/^--parse-only$/", $arg) === 1) {
                add_attrib($argtype->parse_only);
            }
            else if (preg_match("/^--int-only$/", $arg) === 1) {
                add_attrib($argtype->int_only);
            }
            else if (preg_match("/^--jexampath=.+$/", $arg) === 1) {
                add_attrib($argtype->jexampath);
                $argtype->jexam_path = preg_replace("/^--jexampath=/", "", $arg);
            }
            else if (preg_match("/^--noclean$/", $arg) === 1) {
                add_attrib($argtype->noclean);
            }
            else {
                // bad parameter
                error_handle(10);
            }
        }
        
    }


function test_main(): void
{
    global $correct_tests_count, $total_tests_count, $correct_tests_html, $incorrect_tests_html;

    ini_set('display_errors', 'stderr');

    $argtype = new Argtype();
    argtype_init($argtype);

    // generating html on user output
    echo "
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <title>Tests</title>
</head>
<body>
    <style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono&display=swap');
</style>";

    parse_args_test($argtype);
    run_tests($argtype);
    $failed_tests_count = $total_tests_count - $correct_tests_count;
    if (!$argtype->noclean) {
        shell_exec("rm *.out *.src *.rc *.in");
    }

    // html, cont.
    echo "
    <h1 class=\"total_tests\">Passed tests: <span class=\"passed_tests tests\">$correct_tests_count</span>/$total_tests_count</h1>
    <h2 class=\"total_tests\">Failed tests: <span class=\"failed_tests tests\">$failed_tests_count</span>/$total_tests_count</h2>
    ";
    if ($correct_tests_count == $total_tests_count) {
        echo "<h2 class=\"passed_tests\">All tests passed successfully!</h2>";
    }

    echo "
    <div style=\"overflow-y:auto;\" class=\"file_table center\">
      <table>
        <th>
            Passed tests
        </th>
        $correct_tests_html
      </table>
    </div>
    <div style=\"overflow-y:auto;\" class=\"file_table center\">
      <table>
        <th>
            Failed tests
        </th>
        $incorrect_tests_html
      </table>
    </div>
    <style>
        html {
           font-family: 'Space Mono', monospace;
           text-align:center;
        }
        .total_tests {
            padding-left:0;
            margin-left:0;
            border:3px solid #A4E4FF;
        }
        .passed_tests {
            color:green;
        }
        .failed_tests {
            color:#b31717;
        }
        .total_tests {
            text-align:center;
            background-color:#93CDE5;
            color:#293940;
        }
        .file_table {
            height: 200px;
            width: 600px;
            color: white;
            border: 1px dashed black;
        }
        table {
        	margin: auto;
        }
        th {
        	border: 3px solid black;
            text-transform:uppercase;
            padding-left: 5px;
            padding-right: 5px;
            color: #f249c8;
        }
        html {
            background-color:#293940;
        }
        .center {
        	margin: auto;
        }
    </style>
</body>
</html>
";

exit(0);
}
test_main();
