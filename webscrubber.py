from bs4 import BeautifulSoup
import urllib
import pandas as pd
import googlemaps
import sqlite3 as lite
import pickle


def processLink(soup,list):
    letters = soup.find_all("section", class_="listing_info")
    letters2 = soup.find_all("section", class_="listing_specs")
    for i in range(0,len(letters)):
        try:
            bed = letters2[i].find(class_="icon bed-icon").get_text()
            price = letters2[i].find(class_="icon wallet-icon").get_text()
            address = letters[i].h3.get_text()
            link = letters[i].a['href']
            list.append([address,bed,price,link])
        except: 
             print "Oops!  That was no valid number.  Try again..."
            
    return list

def GoogleC(loc):
    gmaps = googlemaps.Client(key='')
    geocode_result = gmaps.geocode(address=loc,language='python')
    lat = geocode_result[0]['geometry']['location']['lat']
    lng = geocode_result[0]['geometry']['location']['lng']
    for e in geocode_result[0]['address_components']:
        if e['types'] == [u'postal_code']:
            zipcode = int(e['long_name'])
    return lat, lng



def myGeocode(addr,gmaps):
    geocode_result = gmaps.geocode(address = addr,components = {'locality': 'New York','country': 'US'})
    lat=geocode_result[0]['geometry']['location']['lat']
    lng=geocode_result[0]['geometry']['location']['lng']
    return (lat,lng)
    
    
    
    
#Get zipcodes from 311 database
conn = lite.connect('311sample.db')
c = conn.cursor()    
sqlq = "SELECT Distinct IncidentZip FROM complains "
PDLIGHT = pd.read_sql_query(sqlq, conn)
zips = PDLIGHT.values
zips = zips[zips>100]
f = open('key.txt', 'r')
myKey=f.readline()
print(myKey)
gmaps = googlemaps.Client(key=myKey)
zipsGPS=[]
for z in zips:
    temp = myGeocode(str(int(z)),gmaps)
    zipsGPS.append(temp)
  
#For each zip code, obtain 10 pages of listings and save to  PandaAPT
template3 ='https://www.rentjungle.com/new-york-apartments-and-houses-for-rent/page:%d/cla:%f/clo:%f/'
a = []
pages = 10
for z in zipsGPS:
    count = count + 1
    for i in range(1,pages):
        link = template3%(i,z[0],z[1])
        try:
            r = urllib.urlopen(link)
        except:
            print('socket fail')
        soup = BeautifulSoup(r)
        processLink(soup,a)

pda = pd.DataFrame(a)
pda.to_csv("PandaAPT.csv")



#Go through the listings and only keep unique(address) samples 
PDA = pd.read_csv('PandaAPT.csv')
PDA = PDA.values
p = []
d = {}
for e in PDA:
    if(e[1] not in d):
        p.append(e[1:].tolist())
        d[e[1] ]=1
d = []
for e in p:
    template = '<a href="%s"; target="_blank">%s %s</a>'%(e[3],e[1],e[2])
    d.append([score(c,e[0]),e[0],template])

FP = pd.DataFrame(d)
FP.to_csv("CleanListings.csv")
    
