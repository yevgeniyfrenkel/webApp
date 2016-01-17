from bs4 import BeautifulSoup
import urllib
import pandas as pd
import numpy as np
import googlemaps
import sqlite3 as lite
import pickle


def processLink(soup, l):
    # extract bed, price, address and URL from each apartment link
    letters = soup.find_all("section", class_="listing_info")
    letters2 = soup.find_all("section", class_="listing_specs")
    for i2 in range(0, len(letters)):
        try:
            bed = letters2[i2].find(class_="icon bed-icon").get_text()
            price = letters2[i2].find(class_="icon wallet-icon").get_text()
            address = letters[i2].h3.get_text()
            url = letters[i2].a['href']
            l.append([address, bed, price, url])
        except:
            print "Oops!  That was no valid number.  Try again..."

    return l


def googleClientWrapper(loc):
    # wrapper for google map API
    gmaps = googlemaps.Client(key='')
    geocode_result = gmaps.geocode(address=loc, language='python')
    lat = geocode_result[0]['geometry']['location']['lat']
    lng = geocode_result[0]['geometry']['location']['lng']
    #    for e in geocode_result[0]['address_components']:
    #        if e['types'] == [u'postal_code']:
    #            zipcode = int(e['long_name'])
    return lat, lng


def scoreCount(myCoursor, loc):
    # Use count of nearby complaints to score location
    lat, lng = googleClientWrapper(loc)
    sqlQuery = "SELECT count(*) FROM complains where ((Latitude-%f)*(Latitude-%f)+(Longitude+%f)*(Longitude+%f))<0.00001" % (
        lat, lat, -lng, -lng)
    myCoursor.execute(sqlQuery)
    query_results = myCoursor.fetchall()
    nComp = query_results[0][0]
    return min(np.round(100.0 * (1.0 / (1.0 + np.log10(nComp)))), 100)


def scoreKDE(b, loc):
    # Use KDE model to score the locations
    lat, lng = googleClientWrapper(loc)
    z = b.score_samples([lat, lng])
    zmin, zmax = (0.80, 6.3)
    z = 50.0 * (1 - (z - zmin) / (zmax - zmin)) + 50
    z = np.min([z, 100.0])
    z = np.max([z, 0])
    return z


def myGeocode(addr, gmaps):
    geocode_result = gmaps.geocode(address=addr, components={'locality': 'New York', 'country': 'US'})
    lat = geocode_result[0]['geometry']['location']['lat']
    lng = geocode_result[0]['geometry']['location']['lng']
    return lat, lng


# Load trained KDE score model
file_Name = "KDEScoreModel"
fileObject = open(file_Name, 'r')
b = pickle.load(fileObject)

# Get zipcodes from 311 database
conn = lite.connect('311sample.db')
c = conn.cursor()
sqlQuery = "SELECT Distinct IncidentZip FROM complains "
zipsRaw = pd.read_sql_query(sqlQuery, conn)
zips = zipsRaw.values
zips = zips[zips > 100]

f = open('key.txt', 'r')
myKey = f.readline()
print(myKey)
gmaps = googlemaps.Client(key=myKey)
zipsGPS = []

print('Geocoding %i zip codes' % len(zips))
for z in zips:
    print('geocoding')
    temp = myGeocode(str(int(z)), gmaps)
    zipsGPS.append(temp)

# For each zip code, obtain 10 pages of listings and save to  PandaAPT
pageTemplate = 'https://www.rentjungle.com/new-york-apartments-and-houses-for-rent/page:%d/cla:%f/clo:%f/'
a = []
pages = 10
print('%i zipcodes in the database' % len(zipsGPS))

count = 0
for z in zipsGPS:
    count = count + 1
    print(count)
    for i in range(1, pages):
        link = pageTemplate % (i, z[0], z[1])
        try:
            r = urllib.urlopen(link)
        except:
            print('socket fail')
        soup = BeautifulSoup(r)
        processLink(soup, a)

pda = pd.DataFrame(a)
pda.to_csv("PandaAPT.csv")

# Go through the listings and only keep unique(address) samples
df = pd.read_csv('PandaAPT.csv')
df = df.values
p = []
d = {}
for e in df:
    if e[1] not in d:
        p.append(e[1:].tolist())
        d[e[1]] = 1
# Use KDE score model to evaluate apartments format the output for google fusion table
d = []
for e in p:
    template = '<a href="%s"; target="_blank">%s %s</a>' % (e[3], e[1], e[2])
    d.append([int(scoreKDE(b, e[0])), e[0], template])

FP = pd.DataFrame(d)
FP.to_csv("CleanListingsKDE.csv")
