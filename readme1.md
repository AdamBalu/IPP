## Implementačná dokumentácia k 1. úlohe do IPP 2021/2022
### Meno a priezvisko: Adam Balušeskul
### Login: xbalus01

## Implementácia
Skript `parse.php` číta štandardný vstup riadok po riadku. Na veľkú väčšinu operácií sú využité funkcie pre regulárne výrazy. Funkcia `preg_match()`, ktorá slúži na vyhľadanie istej postupnosti znakov v stringu (regulárneho výrazu) a `preg_replace()`, ktorá slúži na nahradenie vyhľadávaného podreťazca vlastným podreťazcom.

Chyby behu programu, syntaktické, lexikálne a iné sú spracované funkciou `error_handle()`, ktorá ich vypisuje na štandardný chybový výstup.

Funkcia `arg_check()` zisťuje, či sú argumenty programu zadané v správnom formáte.

Po odstránení komentárov a newline charakterov zo vstupného riadka je tento riadok pripravený na dekompozíciu. Na rozdelenie načítaného riadku podľa whitespace charakterov bola použitá ďalšia regex-ová funkcia `preg_split()`.

Vo funkcii `choose_by_args()` následne prebieha triedenie inštrukcií podľa počtu a typu ich argumentov. Pre každý takýto typ inštrukcie je potom vytvorená vlastná funkcia - `one_arg_var()`, `two_arg_var_type()` atď., ktorá posiela jednotlivé argumenty na lexikálnu a syntaktickú kontrolu podľa ich typu. Ak prebehne kontrola bezproblémovo, uloží túto inštrukciu do výstupnej XML reprezentácie programu.

Funkcie začínajúce kľúčovým slovom `match` kontrolujú lexikálnu správnosť pomocou regulárnych výrazov a v prípade konštánt kontrolujú syntax pomocou funkcie `check_const_syntax()`, ktorá tiež využíva regulárne výrazy.

## Bonusové rozšírenie
Zahrnuté je aj rozšírenie **stats**. Štatistiky sú uchovávané v globálnej triede `Stats`, počítajú sa v priebehu programu a po skončení lexikálnej a syntaktickej kontroly sa v prípade zadaných správnych argumentov programu vypíšu do zadaného súboru. Skoky, ktoré odkazujú na budúce návestia, prípadne neexistujúce, sú riešené vo funkcii `check_forward_labels()`. Počas behu programu sa ukladajú navštívené návestia a na konci sa zisťuje, či sa v nich navštívené skoky nachádzajú.