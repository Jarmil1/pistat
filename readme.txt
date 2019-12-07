Pirátské statistiky
=========================================================================

získává časové řady z nedatabázových veřejných zdrojů: csv souborů apod.

statistiky jsou vytvářeny na denní bázi: 
1) zjistit hodnotu platnou pro daný den 
2) uložit ji do do mysql databáze
	
z této databáze si hodnoty může brát libovolný zobrazovací modul 
(např grafana).
zároveň jsou z nich vytvářeny statické stránky s grafy, viz níže.


URL adresy a API
=========================================================================

Výstupy programu (grafy a data) jsou dostupné na adrese 
https://jarmil1.github.io/pistat-out/

Data každé sbírané statistiky lze získat ve formě CSV souboru,
URL tohoto souboru je na stránce každé statistiky pod nadpisem 
"Zdrojová data ve formátu CSV"

například: 
https://jarmil1.github.io/pistat-out/BALANCE_2701446039.csv


Zdroje dat a způsob jejich získávání:
=========================================================================

zůstatky na účtech: z výpisu transparentního účtu na fio.cz, web scrapping
        seznam účtů získáván ze stránky na wiki FO.
twitter: z veřejné stránky daného uživatele na twitter.com, web scrapping
youtube: z veřejné stránky daného uživatele nebo kanálu
         na youtube.com, web scrapping
počet členů: z výpisu počtu členů příslušné skupiny na forum.pirati.cz,
         web scrapping   


Konfigurace
=========================================================================
Seznam sledovaných twitter účtů lze editovat v projektu 
https://github.com/Jarmil1/pistat-conf


instalace a spuštění ve venvu
=========================================================================

1) stáhni projekt
2) přejmenuj credentials_distrib.py na credentials.py
3) doplň do credentials.py správné přihlašovací údaje


spuštění ve venvu
=========================================================================

1) doinstaluj tkinter, viz install.sh
2) nainstaluj venv spustenim bash install.sh
3) ve venv spusť pistat.py
4) pro pravidelné vytváření statistik spouštěj pistat.py cronem. 
   nevadí, pokud by se tento modul spouštěl paralelně z více míst
   (klíčem v db je datum, tekže nedojde k duplikování hodnot)


sestavení a spuštění v Dockeru
=========================================================================

1) v kořenovém adresáři pistat spusť docker build --tag=pistat .
2) spusť docker run pistat

Publikace dockeru na server:
docker save pistat > ~/img.tar
scp ~/img.tar $PIRTEST:~

na serveru:
cat ~/img.tar | docker load


chceš se přidat?
=========================================================================

potřebné znalosti: 
	python3.*, git, pep8

doporučená četba:
	mastering python / rick van hattem
	paulgraham.com essays / paul graham
	pro git / scott chacon
	síla jednoduchosti / leo babauta
	
jak se zapojit
=========================================================================

1) zprovozni modul u sebe
2a) vyber si issue ze seznamu nebo
2b) začni dělat na statistice, kterou potřebuješ
3) každopádně si vytvoř novou větev 
4) po skončení vývoje do ní zaintegruj master větev
5) pošli merge request
