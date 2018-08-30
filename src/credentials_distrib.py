#! /usr/bin/python3

""" Credentials - pristupove udaje k pouzivanym zdrojum.

	Kazdy credential je slovnik, s temito klici:
	
		host			url zdoje	
		databasename 	jmeno databaze, je-li zdojem MySql databaze
		username		
		password
	
	
"""

# testovaci mysql databaze pro pistat, zadarmiko gdesi v cloudu
FREEDB = {	"databasename": 'xxxxxxxxxxxxxxxxxx',
			"host": 		'sql2.freemysqlhosting.net',
			"username": 	'xxxxxxxxxxxxxxxxxx',
			"password": 	'xxxxxxxxxxxxxxxxxx'
		 }