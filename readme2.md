## Implementačná dokumentácia k 2. úlohe do IPP 2021/2022
### Meno a priezvisko: Adam Balušeskul
### Login: xbalus01

## Implementácia interpret.py
### Ošetrovanie chybových hlášok
Chybové hlášky sú v skripte riešené pomocou zabudovanej funkcionality jazyku
Python - `try` a `except`. Každý druh chyby má okrem návratového kódu aj 
vlastnú chybovú správu, ktorá sa vypíše na štandardný chybový výstup.
Tieto chybové správy sú definované vo funkcii `raise_err()` a ich návratové kódy
ďalej vo funkcii `exit_err()`.

Pri zaznamenaní chyby programu sa vyvolá výnimka, 
ktorá je zachytená funkciou `catch_exceptions_and_launch()`. Táto funkcia slúži aj
ako spúšťacia funkcia zvyšku programu.

### Globálne premenné a konštanty
Globálne premenné pozostávajú z rámcov (`GF` - globálny, `TF` - dočasný, `LF` - lokálny),
zásobníkov (zásobník `FS` - rámcov, `CS` - volaní, `DS` - dátový) a špeciálneho slovníka `LD`,
do ktorého sa vo funkcii `fill_label_dict_with_labels()` ukladajú návestia v podobe `{"názov_návestia": poradie_inštrukcie}`.

Konštanty tvoria listy, ktoré spájajú operačné kódy inštrukcií s rovnakým
počtom argumentov. Do zoznamu konštánt patrí aj `var_types` - zoznam možných typov premennej.

### Kontrola sémantiky XML vstupu
Hlavná kontrola sémantiky prebieha vo funkcii `semantic_checks()`.
Tu sa zisťuje, či majú argumenty inštrukcií správne priradené typy. Dôležitú časť
sémantickej kontroly tvorí funkcia `check_symb_sem()`, ktorá pri daných príležitostiach 
kontroluje správnosť typu `symb`. Význam
sa ďalej rieši aj vo zvyšku skriptu, kde sa príležitostne objavujú kontroly na správne
typy hodnôt, a pri prípadných nesprávnych hodnotách vyvolávajú patričné výnimky.

### Spracovávanie inštrukcií
Funkcia, ktorá ma na starosti správu inštrukcií - `eval_instructions()` - volá
jednu z možných podfunkcií, ktoré sú triedené podľa počtu argumentov,
ktoré daná inštrukcia obsahuje. Volanie patričnej funkcie sa určuje podľa 
operačného kódu inštrukcie (premenná `i_opcode`). 

Pre väčšinu zložitejších inštrukcií sú vytvorené vlastné funkcie 
(`arithmetic_operations_eval()`, `bool_operations_eval()` atď.) 
aby sa zachovala čitateľnosť hlavných funkcií programu.

## Implementácia test.php

### Narábanie s parametrami programu
Parametre programu sa spracúvajú pomocou dátovej štruktúry - triedy `Argtype`, ktorá je inicializovaná
funkciou `argtype_init()` a
ktorá v sebe drží informácie o tom, aký parameter bol definovaný, prípadne aký názov súboru tento
parameter obsahoval. Mená súborov sa už dopredu inicializujú na hodnoty, ktoré by obsahovali ak daný parameter,
obsahujúci meno súboru, nie je zadaný.

Tieto dopredu definované hodnoty upravuje funkcia `parse_args_test()`, ktorá porovnáva každý
z parametrov s očakávanými výrazmi pomocou regulárnych výrazov (regexov). Filtrovanie
názvov súborov od názvu parametrov je takisto riešené pomocou funkcií pracujúcich
s regulárnymi výrazmi (`preg_replace()`).

### Otváranie súborov a porovnávanie výstupov

O tom, aké súbory sa budú otvárať (skript ponúka možnosť rekurzívneho testovania všetkých
podpriečinkov) sa rozhoduje vo funkcii `run_tests()`.

Nasledujúce funkcie
```php
function open_file($f, Argtype $argtype): void
function open_file_int($f, $argtype): void
function both($f, Argtype $argtype): void
```
fungujú na rovnakom princípe. Ich úlohou je spustiť program `parse.php`/`interpret.py`
nad zadanými vstupmi a porovnať ich výstupy. Funkcia `both()` spúšťa najprv parser
a jeho výstup dáva na vstup interpretu, takže tým kontroluje funkcionalitu obidvoch skriptov.

### Generovanie HTML

HTML sa na štandardný výstup generuje pomocou príkazu `echo` v základnej funkcii 
`test_main()`. HTML obsahuje aj niektoré prvky CSS. Počet testov, ktoré prešli
správne, určuje globálna premenná `$correct_tests_count`, a celkový počet testov je uložený v globálnej premennej `$total_tests_count`.