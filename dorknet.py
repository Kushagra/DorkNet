#!/usr/bin/env python2.7

import argparse
import sys
import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from blessings import Terminal

t = Terminal()


# Check for args, print logo and usage
if not len(sys.argv[1:]):
    print t.cyan("""
 ____          _   _____     _
|    \ ___ ___| |_|   | |___| |_
|  |  | . |  _| '_| | | | -_|  _|
|____/|___|_| |_,_|_|___|___|_|

Welcome to DorkNet.

To start using this script please provide one or more command
line arguments and their corresponding value, where applicable.
To display all options available use -h or --help.

Example:
DorkNet.py -h
DorkNet.py -d inurl:show.php?id= --verbose\n""")

    sys.exit(0)


# Handle command line arguments
parser = argparse.ArgumentParser(description="Use this script and dorks to find vulnerable web applications.")
group = parser.add_mutually_exclusive_group()
group.add_argument("-d", "--dork", help="		specify the dork you wish to use\n")
group.add_argument("-l", "--list", help="		specify path to list with dorks\n")
parser.add_argument("-p", "--pages", type=int, help="		no. of pages to scrap\n", required=True)
parser.add_argument("-v", "--verbose", action="store_true", help="		toggle verbosity\n")
args = parser.parse_args()

dork_list = []

p = args.pages

print "pages set by user: %s" % (p)

# Dork list processing
if args.list:
	print "\n[" + t.green("+") + "]Reading in list from: " + args.list + "\n\n"
	try:
		with open(args.list, "r") as ins:
			for line in ins:
				dork_list.append(line)

				if args.verbose == True:
					print "[" + t.magenta("~") + "]" + line

	except IOError as e:
		print "\n[" + t.red("!") + "]Could not read dork list"
		if args.verbose == True:
			print "\nAn IO Error was raised with the following error message: "
			print "\n %s" % (e)

else:
    dork_list.append(args.dork)

print dork_list


print "\n[" + t.green("+") + "]Would you like DorkNet to proxy it's connection to the search engine?"
query = raw_input("[Y]es/[N]o: ").lower()

if query == 'y':
	IP = raw_input("\n[" + t.green("+") + "]Please enter the proxy host IP: ")
	PORT = raw_input("\n[" + t.green("+") + "]Please enter the proxy port: ")
	set_proxy = True
elif query == 'n':
	print "\n[" + t.green("+") + "]Establishing unproxied connection...\n"
	set_proxy = False
else:
	print "\n[" + t.red("!") + "]Unhandled option, defaulting to unproxied connection..."
	set_proxy = False


# Web Driver Proxy
def proxy(PROXY_HOST,PROXY_PORT):
	fp = webdriver.FirefoxProfile()
	print "[" + t.green("+") + "]Proxy host set to: " + PROXY_HOST
	print "[" + t.green("+") + "]Proxy port set to: " + PROXY_PORT
	print "\n[" + t.green("+") + "]Establishing connection..."
	fp.set_preference("network.proxy.type", 1)
	fp.set_preference("network.proxy.http",PROXY_HOST)
	fp.set_preference("network.proxy.http_port",int(PROXY_PORT))
	fp.set_preference("general.useragent.override","'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'")
	fp.update_preferences()
	return webdriver.Firefox(firefox_profile=fp)


# Function to generate and process results based on input
def search():
	link_list = []

	if set_proxy == True:
		driver = proxy(IP, PORT)
	else:
		driver = webdriver.Firefox()

	for int in range(1):
		try:
			driver.get("http://google.com")
		except Exception as e:
			print "\n[" + t.red("!") + "]A connection could not be established"
			if args.verbose == True:
				print "An error was raised with the following error message: "
				print "\n %s" % (e)
				break
				driver.quit()
				sys.exit(0)

		assert "Google" in driver.title
		for items in dork_list:
			elem = driver.find_element_by_name("q")
			elem.clear()
			elem.send_keys(items)
			elem.send_keys(Keys.RETURN)
			#time.sleep(1)

			#To-do: Create a verification statement to check if a captcha is presented. If true, then pause the script with raw_input()

			try:
				WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "r")))
			except Exception as e:
				driver.quit()
				print "\n[" + t.red("!") + "]Detecting page source elements failed/timed out.\n"

				if args.verbose == True:
					print "An error was raised with the following error message: "
					print "\n %s" % (e)

				time.sleep(1)
				continue

			""""""
			# to check if results "omitted" error present on first page

			if "repeat the search with the omitted results included" in driver.page_source:
				driver.find_element_by_xpath("/html/body/div[5]/div[3]/div[10]/div[1]/div[2]/div/div[4]/div/div/div[2]/p/i/a").click()
			else:
				continue

			""""""

			assert "No results found" not in driver.page_source
			if "No results found" in driver.page_source:
				continue

			count = 1
			while (count <= p):
				links = driver.find_elements_by_xpath("//h3//a[@href]")
				for elem in links:
					link_list.append(elem.get_attribute("href"))

				#To-do: Create a verification statement to check if a captcha is presented. If yes, then pause the script with raw_input()
				#To-do: Create a verification statement to check when there are no more result page - no next page button present

				driver.find_element_by_xpath("//*[@id='pnnext']").click()
				count = count + 1
				print count

	driver.quit()
	return link_list

proc_one = search()

with open("results.log", "ab") as outfile:
	for item in proc_one:
		outfile.write("%s\n" % item)

if args.verbose == True:
	with open("results.log", "r") as infile:
		for line in infile:
			print "[" + t.magenta("~") + "]" + line


print "\n\n[" + t.green("+") + "]Done. Results have been saved to a textfile, in the current directory as %s for further processing.\n" % outfile
