# Trademark Violations - SERP Monitoring
# Version 0.01 (03/04/2020)
# Phillip Molock | phmolock@microsoft.com
# Andrew Hoke | Andrew.Hoke@microsoft.com

from selenium import webdriver
from urllib.parse import urlparse
from random import randint
import csv, time

# Enter the customer home website, name (for trademark check), and search query

settings = {
    'txtFile': 'trademarks.txt',
    'output': 'output'
}
# Tracking details for ATAM Script Tracker
class Atamlogger:
    def __init__(self, scriptid, scriptname, scriptowner, apikey):
        self.urlpath = 'https://techsolutionsapi.azurewebsites.net/v1/logs'
        self.headers = {'key': apikey}
        self.data = {'username': self.getUser(),
                    'scriptid': scriptid,
                    'scriptname': scriptname,
                    'scriptowner': scriptowner
                    }
        self.call()

    def call(self):
        try:
            r = requests.post(url=self.urlpath, headers=self.headers, json=self.data)
            print(r.text)
        except:
            print('error - request failed')

    def getUser(self):
        u = 'unknown'
        try:
            u = getuser()
        except:
            print('error - could not find username')
        finally:
            return u

def checkTrademarks(trademarksToCheck):
    # Establish webdriver 
    browser = webdriver.Chrome()
    trademarkViolations = {}

    for homepage, trademarkDetails in trademarksToCheck.items():
        trademarks = trademarkDetails['trademarks']
        searchQueries = trademarkDetails['searchQueries']
        print(f"\nPerforming trademark violation check\n\tTrademarks: {trademarks}")
        
        for searchQuery in searchQueries:
            searchQuery = searchQuery.strip()
            print(f"\nSearch query: {searchQuery}\n")
            browser.get('https://www.bing.com')
            # Find bing search box and search for customer's name
            bingSearchBox = browser.find_element_by_id('sb_form_q')
            bingSearchBox.send_keys(searchQuery)
            bingSearchBox.submit()

            # Find the list of ads to loop through 
            bingMainLineAds = browser.find_elements_by_xpath("//li[@class='b_ad']/ul/li")
            time.sleep(3)
            mainLineCount = 0
            if len(bingMainLineAds) == 0:
                print("\tNo ads returned for this search query.")
                continue
            for ad in bingMainLineAds:
                # Check if a product ads carousel exists
                try:
                    divs = ad.find_element_by_xpath(".//div[contains(@class, 'carousel')]")
                    continue
                except:
                    # If there is an error finding a div with a class containing carousel then it is not the product ad carousel
                    pass
                
                mainLineCount += 1
                try:    
                    displayUrl = ad.find_element_by_xpath(".//div[@class='b_adurl']").text
                except Exception as e:
                    continue
                    print(f"\tError finding the Display URL of the ad:\n\t{e}")

                displayUrlNetloc = urlparse(displayUrl).netloc.lower()
                homepageNetloc = urlparse(homepage).netloc.lower()
                print(f"Mainline {mainLineCount}:\n\t{displayUrl}")
                
                if displayUrlNetloc == homepageNetloc:
                    continue
                else:
                    for trademark in trademarks:
                        if (trademark.lower().strip() in ad.text.lower()):
                            rLink = ad.find_element_by_xpath(".//a[contains(@href, 'https://www.bing.com/aclk?')]").get_attribute("href")
                            trademarkViolations[displayUrl] = (trademark, rLink)
                            print(f"\tFound potential trademark violation for r-link: {rLink}")


    # If any trademark violations were detected, write them to a CSV
    if len(trademarkViolations) > 0:
        outputName = f"TM Violations {randint(100,999)}.csv"
        with open(outputName, "w", newline="") as csvOut:
            csvWriter = csv.writer(csvOut, delimiter=',')
            csvWriter.writerow(['DisplayURL', 'TrademarkViolated', 'rLink'])
            for displayUrl, violationDetails in trademarkViolations.items():
                csvWriter.writerow([displayUrl, violationDetails[0], violationDetails[1]])
        print(f"Output written to: {outputName}")

def readTrademarksFromText():
    trademarksToCheck = {}
    with open(settings['txtFile'], 'r', errors='ignore') as txtIn:
        header = next(txtIn).replace('\n','').split('\t')
        for row in txtIn:
            row = row.replace('\n','').split('\t')
            trademarks = list(filter(lambda x: x != '', row[header.index('trademarks')].split(',')))
            homepage = row[header.index('homepage')]
            searchQueries = list(filter(lambda x: x != '', row[header.index('searchQueries')].split(',')))
            trademarksToCheck[homepage] = {
                'trademarks': trademarks,
                'searchQueries': searchQueries
            }
    return trademarksToCheck

def main():
    l = Atamlogger(1001, 'trademarkviolations', 'phmolock', '82302af0')
    trademarksToCheck = readTrademarksFromText()
    checkTrademarks(trademarksToCheck)

if __name__ == "__main__":
    main()
