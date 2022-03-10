<?php

    class Argtype {
        public $help;
        public $directory;
        public $recursive;
        public $parse_script;
        public $int_script;
        public $parse_only;
        public $int_only;
        public $jexampath;
        public $noclean;
        public $directory_path;
        public $jexam_path;
        public $parse_script_file;
        public $int_script_file;
    }


    $correct_tests_count = 0;
    $total_tests_count = 0;

    
    if (!defined('STDERR')) { define('STDERR', fopen('php://stderr', "w")); }

    function error_handle(int $err_num) {
        fwrite(STDERR, "Error $err_num" . PHP_EOL);
        exit($err_num);
    }

    function print_help_1() {
        print("Help! XD\n");
    }

    function argtype_init(Argtype $argtype) {
        $argtype->help = 0;
        $argtype->directory = 0;
        $argtype->recursive = 0;
        $argtype->parse_script = 0;
        $argtype->int_script = 0;
        $argtype->parse_only = 0;
        $argtype->int_only = 0;
        $argtype->jexampath = 0;
        $argtype->noclean = 0;
        $argtype->directory_path = ".";
        $argtype->jexam_path = "/pub/courses/ipp/jexamxml/";
        $argtype->parse_script_file = "parse.php";
        $argtype->int_script_file = "interpret.py";
    }

    function argtype_check_occurences(Argtype $argtype) {
        if (
        $argtype->help > 1 ||
        $argtype->directory > 1 ||
        $argtype->recursive > 1 ||
        $argtype->parse_script > 1 ||
        $argtype->int_script > 1 ||
        $argtype->parse_only > 1 ||
        $argtype->int_only > 1 ||
        $argtype->jexampath > 1 ||
        $argtype->noclean > 1) { error_handle(10); }
    }

    function open_file($f) {
        GLOBAL $total_tests_count, $correct_tests_count;
        if (preg_match("/^.*\.src$/", $f) === 1) {
            $total_tests_count++;
            shell_exec('php parse.php < ' . $f . ' > test.out; echo $? | tr -d "\n" > test.rc');
            $f_stripped = preg_replace("/\.src$/", "", $f);

            $f_stripped_rc = $f_stripped . ".rc";
            $f_stripped_out = $f_stripped . ".out";
            exec("diff -q \"$f_stripped_rc\" \"test.rc\"", $dump, $diff);
            if (!$diff) {
                $correct_tests_count++;
                // exec("diff -q \"$f_stripped_out\" \"test.out\"", $dump, $o_diff);
                $output = file_get_contents("test.rc");
                if ($output == "0") {
                    exec("java -jar jexamxml/jexamxml.jar test.out $f_stripped_out delta.xml options", $dump, $xml_diff);
                    if ($xml_diff !== 0) {
                        echo "NOK" . $f . "\n";
                        exit(1);
                    }
                    else {
                        echo "OK\n";
                    }
                }
                else {
                    echo "OK\n";
                }
            }
            else {
                echo "NOK $f\n";
                exit(1);
            }  
        }
    }

    function run_tests(Argtype $argtype) {
        global $argc;
        if ($argtype->help) {
            if ($argc > 2) { error_handle(10); }
            print_help();
        }
    
        // path is not a directory
        if (!is_dir($argtype->directory_path)) { error_handle(41); }

        // recursively go through all files in folder
        if ($argtype->recursive) {
            $dir_iterator = new RecursiveDirectoryIterator($argtype->directory_path);
            $iterator = new RecursiveIteratorIterator($dir_iterator, RecursiveIteratorIterator::SELF_FIRST);
            foreach ($iterator as $file) {
                if ($file->isFile()) {
                    open_file($file);
                }
            }
        }

        // only go through files in given path directory
        else if ($dh = opendir($argtype->directory_path)) {
            while (($file = readdir($dh)) !== false) {
                $full_path = $argtype->directory_path . "/" . $file;
                open_file($full_path);
            }
            closedir($dh);
        }
        else { error_handle(41); }

        
    }

    function parse_args_test(Argtype $argtype) {
        global $argc, $argv;

        // no arguments
        if ($argc < 2) { return 0; }
        
        for ($i = 1; $i < count($argv); $i++) {
            $arg = $argv[$i];
            if (preg_match("/^\-\-help$/", $arg) === 1)                 { $argtype->help += 1; }
            else if (preg_match("/^\-\-directory=.+$/", $arg) === 1)    { $argtype->directory += 1; $argtype->directory_path = preg_replace("/^\-\-directory=/", "", $arg); }
            else if (preg_match("/^\-\-recursive$/", $arg) === 1)       { $argtype->recursive += 1; }
            else if (preg_match("/^\-\-parse-script=.+$/", $arg) === 1) { $argtype->parse_script += 1; $argtype->parse_script_file = preg_replace("/^\-\-parse-script=/", "", $arg); }
            else if (preg_match("/^\-\-int-script=.+$/", $arg) === 1)   { $argtype->int_script += 1; $argtype->int_script_file = preg_replace("/^\-\-int-script=/", "", $arg); }
            else if (preg_match("/^\-\-parse-only$/", $arg) === 1)      { $argtype->parse_only += 1; }
            else if (preg_match("/^\-\-int-only$/", $arg) === 1)        { $argtype->int_only += 1; }
            else if (preg_match("/^\-\-jexampath=.+$/", $arg) === 1)    { $argtype->jexampath += 1; $argtype->jexam_path = preg_replace("/^\-\-jexampath=/", "", $arg); }
            else if (preg_match("/^\-\-noclean$/", $arg) === 1)         { $argtype->noclean += 1; }
            else { error_handle(10); }
            argtype_check_occurences($argtype);
        }
        
    }

    function test_main() {
        GLOBAL $correct_tests_count, $total_tests_count;
        ini_set('display_errors', 'stderr');

        $argtype = new Argtype();
        argtype_init($argtype);

        parse_args_test($argtype);
        run_tests($argtype);
        echo "Total tests passed: $correct_tests_count/$total_tests_count\n";
        exit(0);
    }
    test_main();
?>