Pirátské statistiky
=========================================================================

Získává statistiky z nedatabázových veřejných zdrojů: csv souborů apod.

Statistiky jsou vytvářeny na denní bázi: spouští se cronem 1x denně.

Modul má pro každou zjišťovanou statistiku na starost: 
1) zjistit hodnotu platnou pro tento den 
2) uložit ji do do MySql databáze
	
Z této databáze si hodnoty bere zobrazovací modul Grafana.

Instalace a spuštění
=========================================================================

1) Stáhni projekt
2) Přejmenuj credentials_distrib.py na credentials.py
3) Doplň do credentials.py správné přihlašovací údaje
4) Spusť pistat.py
5) Pro pravidelné vytváření statistik spouštěj pistat.py cronem. 
   Nevadí, pokud by se tento modul spouštěl paralelně z více míst
   (klíčem v db je datum, tekže nedojde k duplikování hodnot)

Přidávání nových statistik
=========================================================================

1) prohlédni si pistat.py
2) vymysli své statistice pěkné popisné id
3) buď kreativní   
4) nauč se python


