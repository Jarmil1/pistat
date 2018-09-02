Pirátské statistiky
=========================================================================

získává statistiky z nedatabázových veřejných zdrojů: csv souborů apod.

statistiky jsou vytvářeny na denní bázi: spouští se cronem 1x denně.

modul má pro každou zjišťovanou statistiku na starost: 
1) zjistit hodnotu platnou pro tento den 
2) uložit ji do do mysql databáze
	
z této databáze si hodnoty bere zobrazovací modul grafana.

instalace a spuštění
=========================================================================

1) stáhni projekt
2) přejmenuj credentials_distrib.py na credentials.py
3) doplň do credentials.py správné přihlašovací údaje
4) spusť pistat.py
5) pro pravidelné vytváření statistik spouštěj pistat.py cronem. 
   nevadí, pokud by se tento modul spouštěl paralelně z více míst
   (klíčem v db je datum, tekže nedojde k duplikování hodnot)

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
