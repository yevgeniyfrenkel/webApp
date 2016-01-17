from flask import render_template, request
from app import app
import sqlite3 as lite
import numpy as np
import googlemaps
from clusterwarn import clusterwarning
import pickle

# import the KDE scoring module
file_Name = "testfile"
fileObject = open(file_Name, 'r')
bKDE = pickle.load(fileObject)
fileObject.close()

# import the KDE scoring module
file_Name2 = "key.txt"
fileObject = open(file_Name2, 'r')
googleKey = fileObject.read()
print(googleKey)
fileObject.close()

# connect to 311 database
conn = lite.connect('311sample.db')
aNYC = []


@app.route('/about')
def cities_input3():
    return render_template("about.html")


@app.route('/')
def cities_input2():
    return render_template("input.html")


@app.route('/index')
def index():
    return render_template("input.html")


@app.route('/input')
def cities_input():
    return render_template("input.html")


@app.route('/output')
def cities_output(PD=[], conn=conn, kde=bKDE, gkey=googleKey):
    # pull address 'ID' from input field
    city = request.args.get('ID')

    # convert address into the long, lat format
    gmaps = googlemaps.Client(key=gkey)
    geocode_result = gmaps.geocode(address=city, components={'locality': 'New York', 'country': 'US'})
    lat = geocode_result[0]['geometry']['location']['lat']
    lng = geocode_result[0]['geometry']['location']['lng']
    zipcode = 10007

    for e in geocode_result[0]['address_components']:
        if e['types'] == [u'postal_code']:
            zipcode = int(e['long_name'])
    if type(zipcode) != type(1):
        zipcode = 10007

    # connect to complaints datable ans pull all the complaints close ot the entered location
    conn = lite.connect('311sample.db')
    c = conn.cursor()
    c.execute(
        "SELECT  count(*) FROM complains where ((Latitude-%f)*(Latitude-%f)+(Longitude+%f)*(Longitude+%f))<0.00003" % (
        lat, lat, -lng, -lng))
    lsum = c.fetchall()
    lsum = lsum[0][0]
    c.execute(
        "SELECT Descriptor, 100*count(Descriptor)/(%d), count(Descriptor)/52, color FROM complains where ((Latitude-%f)*(Latitude-%f)+(Longitude+%f)*(Longitude+%f))<0.00003 Group by Descriptor Order by  count(Descriptor) DESC  limit 10" % (
        lsum, lat, lat, -lng, -lng))

    color = -1
    try:
        query_results = c.fetchall()
        color = query_results[0][-1]
        print('compaint color')
        print(color)
    except:
        print('no color found')

    conn2 = lite.connect('Clustersample2.db')
    c2 = conn2.cursor()
    c2.execute(
        "SELECT  count(*) FROM complains where ((Latitude-%f)*(Latitude-%f)+(Longitude+%f)*(Longitude+%f))<0.0000005" % (
        lat, lat, -lng, -lng))
    clusterAlert = c2.fetchall()
    print(clusterAlert)
    NCW = ""

    # just select the city from the world_innodb that the user inputs

    cities = []

    for result in query_results:
        cities.append(dict(name=result[0], country=result[1], population=result[2]))

    z = kde.score_samples([lat, lng])
    # scaling constants
    zmin, zmax = (0.81, 6.33)
    z = 50.0 * (1 - (z - zmin) / (zmax - zmin)) + 50
    z = np.min([z, 100.0])
    z = np.max([z, 0])
    the_result3 = int(z)
    # cluster warming
    NCW = ' '
    if clusterAlert[0][0] != 0:
        NCW = clusterwarning(color, the_result3)
    else:
        NCW = clusterwarning(-1, the_result3)

    return render_template("output.html", cities=cities, the_result3=the_result3, latcnt=lat, lngcnt=lng, ncw=NCW)
