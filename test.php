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

    function print_help() {
        echo
"Test suite is used for gradual testing of the applications parse.php and interpret.py

USAGE: php8.1 test.php [--help] [ARG]
--help
        display this help and exit
ARGs:
--directory=PATH
testy bude hledat v zadaném adresáři (chybí-li tento parametr, skript
prochází aktuální adresář);

--recursive 
testy bude hledat nejen v zadaném adresáři, ale i rekurzivně ve všech jeho
podadresářích;

--parse-script=file
soubor se skriptem v PHP 8.1 pro analýzu zdrojového kódu v IPPcode22 
(chybí-li tento parametr, implicitní hodnotou je parse.php uložený v aktuálním adresáři);

--int-script=file 
soubor se skriptem v Python 3.8 pro interpret XML reprezentace kódu
v IPPcode22 (chybí-li tento parametr, implicitní hodnotou je interpret.py uložený v aktuálním adresáři);

--parse-only
bude testován pouze skript pro analýzu zdrojového kódu v IPPcode22 (tento
parametr se nesmí kombinovat s parametry --int-only a --int-script), výstup s referenčním
výstupem (soubor s příponou out) porovnávejte nástrojem A7Soft JExamXML (viz [2]);

--int-only
bude testován pouze skript pro interpret XML reprezentace kódu v IPPcode22 (tento parametr se nesmí kombinovat s parametry --parse-only, --parse-script
a --jexampath). Vstupní program reprezentován pomocí XML bude v souboru s příponou
src.

--jexampath=path cesta k adresáři obsahující soubor jexamxml.jar s JAR balíčkem s nástrojem A7Soft JExamXML a soubor s konfigurací jménem options. Je-li parametr vynechán,
uvažuje se implicitní umístění /pub/courses/ipp/jexamxml/ na serveru Merlin, kde bude
test.php hodnocen. Koncové lomítko v path je případně nutno doplnit.

--noclean 
během činnosti test.php nebudou mazány pomocné soubory s mezivýsledky, tj.
skript ponechá soubory, které vznikají při práci testovaných skriptů (např. soubor s výsledným
XML po spuštění parse.php atd.).
        \n";
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

    function both($f, $argtype) {
        GLOBAL $total_tests_count, $correct_tests_count;
        if (preg_match("/^.*\.src$/", $f) === 1) {
            $total_tests_count++;
            shell_exec('php parse.php < ' . $f . ' > tests/test.src');
            $f_stripped = preg_replace("/\.src$/", "", $f);
            $input_file = preg_replace("/\.src$/", ".in", $f);
            $output_file = preg_replace("/\.src$/", ".out", $f);
            shell_exec('echo -n >>'. $input_file);
            shell_exec('echo -n >>'. $output_file);
            $wd = getcwd();
            $source_file = "--source=" . $wd . "/tests/test.src";
            $input = "--input=" . $input_file;
            shell_exec('python3.8 interpret.py '. $source_file .' '. $input . '> tests/test.out; echo $? > tests/test.rc');
            
            $f_stripped_rc = $f_stripped . ".rc";
            if (file_get_contents($f_stripped_rc) === false) {
                shell_exec('echo -n >>'. $f_stripped_rc . ';echo 0 | tr -d "\n" > ' . $f_stripped_rc);
            }
            exec("diff -qb \"$f_stripped_rc\" \"tests/test.rc\"", $dump, $diff);
            exec("diff -qb \"$output_file\" \"tests/test.out\"", $dump, $diff2);
            if (!$diff && !$diff2) {
                $correct_tests_count++;
                echo "OK\n";
            }
            else {
                echo "NOK diff1:$diff diff2:$diff2 file: $f\n";
                // exit(1);
            }
        }
    }


    function open_file($f) {
        GLOBAL $total_tests_count, $correct_tests_count;
        if (preg_match("/^.*\.src$/", $f) === 1) {
            $total_tests_count++;
            shell_exec('php parse.php < ' . $f . ' > tests/test.out; echo $? | tr -d "\n" > tests/test.rc');
            $f_stripped = preg_replace("/\.src$/", "", $f);

            $f_stripped_rc = $f_stripped . ".rc";
            $f_stripped_out = $f_stripped . ".out";
            exec("diff -qb \"$f_stripped_rc\" \"tests/test.rc\"", $dump, $diff);
            if (!$diff) {
                $correct_tests_count++;
                // exec("diff -q \"$f_stripped_out\" \"test.out\"", $dump, $o_diff);
                $output = file_get_contents("tests/test.rc");
                if ($output == "0") {
                    exec("java -jar jexamxml/jexamxml.jar tests/test.out $f_stripped_out delta.xml options", $dump, $xml_diff);
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


    function open_file_int($f) {
        GLOBAL $total_tests_count, $correct_tests_count;
        if (preg_match("/^.*\.src$/", $f) === 1) {
            $total_tests_count++;
            $f_stripped = preg_replace("/\.src$/", "", $f);
            // $f_dir = '/' . preg_replace("/\/[^\/]+$/", "/", $f);
            // echo $f_dir . "\n";
            $input_file = preg_replace("/\.src$/", ".in", $f);
            $output_file = preg_replace("/\.src$/", ".out", $f);
            shell_exec('echo -n >>'. $input_file);
            shell_exec('echo -n >>'. $output_file);
            $source_file = "--source=" . $f_stripped . ".src";
            $input = "--input=" . $input_file;
            shell_exec('python3.8 interpret.py '. $source_file .' '. $input . '> tests/test.out; echo $? | tr -d "\n" > tests/test.rc');
            
            $f_stripped_rc = $f_stripped . ".rc";
            if (file_get_contents($f_stripped_rc) === false) {
                shell_exec('echo -n >>'. $f_stripped_rc . ';echo 0 | tr -d "\n" > ' . $f_stripped_rc);
            }
            exec("diff -qb \"$f_stripped_rc\" \"tests/test.rc\"", $dump, $diff);
            exec("diff -qb \"$output_file\" \"tests/test.out\"", $dump, $diff2);
            if (!$diff && !$diff2) {
                $correct_tests_count++;
                echo "OK\n";
            }
            else {
                echo "NOK $f\n";
            }  
        }
    }


    function run_tests(Argtype $argtype) {
        global $argc;
        shell_exec('rm -r tests;mkdir tests');
        if ($argtype->help) {
            if ($argc > 2) { error_handle(10); }
            print_help();
            exit(0);
        }
    
        // path is not a directory
        if (!is_dir($argtype->directory_path)) { error_handle(41); }

        // recursively go through all files in folder
        if ($argtype->recursive) {
            $dir_iterator = new RecursiveDirectoryIterator($argtype->directory_path);
            $iterator = new RecursiveIteratorIterator($dir_iterator, RecursiveIteratorIterator::SELF_FIRST);
            foreach ($iterator as $file) {
                if ($file->isFile()) {
                    if ($argtype->int_only !== 1 && $argtype->parse_only !== 1) {
                        both($file, $argtype);
                    }
                    else if ($argtype->int_only !== 1) {
                        open_file($file);
                    }
                    else if ($argtype->parse_only !== 1) {
                        open_file_int($file);
                    }
                }
            }
        }

        // only go through files in given path directory
        else if ($dh = opendir($argtype->directory_path)) {
            while (($file = readdir($dh)) !== false) {
                $full_path = $argtype->directory_path . "/" . $file;
                if ($argtype->int_only !== 1 && $argtype->parse_only !== 1) {
                    both($full_path, $argtype);
                }
                else if ($argtype->int_only !== 1) {
                    open_file($full_path);
                }
                else if ($argtype->parse_only !== 1) {
                    open_file_int($full_path);
                }
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
        $test_cnt = $correct_tests_count . "/" . $total_tests_count;
        $dom = new DOMDocument('2.0');
        $text = $dom->createElement('p', $test_cnt);
        $dom->appendChild($text);
        echo $dom->saveHTML();
        exit(0);

    }
    test_main();
?>