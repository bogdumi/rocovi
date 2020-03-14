from __future__ import print_function # to avoid issues between Python 2 and 3 printing
from flask import Flask, render_template, jsonify
from markupsafe import escape
from skimage import data, io, color, transform, exposure
from scipy import stats

import re
import numpy as np
import matplotlib.pyplot as plt, mpld3
import pandas as pd
import datetime
import matplotlib
matplotlib.use('Agg')

app = Flask(__name__)

# By default we set figures to be 6"x4" on a 110 dots per inch (DPI) screen 
# (adjust DPI if you have a high res screen!)

def getPoints(a, b, n):
    coordsX = np.random.rand(n)
    coordsY = []
    for x in coordsX:
        e = 0.01 * np.random.randn()
        coordsY.append(a + b * x + e)
    return coordsX, coordsY

def lsr(coordsX, coordsY):
    Y = np.array(coordsY)
    ones = np.ones(len(coordsX))
    X = np.column_stack((ones, 1.4**coordsX))
    A = np.linalg.inv(np.transpose(X).dot(X)).dot(np.transpose(X)).dot(Y)
    return A

def calculateError(coordsX, coordsY, A):
    err = 0
    for x, y in zip(coordsX, coordsY):
        tempY = A[0] + A[1] * x
        err = err + (tempY - y) ** 2
    return err

def graphMeBabyOneMoreTime(country):
    hfont = {'fontname':'Helvetica'}
    f1 = plt.figure(figsize=(10, 5), dpi=110)
    plt.grid()
    plt.style.use('seaborn-whitegrid')
    plt.rcParams['grid.linestyle'] = "dotted"
    plt.ylabel('Cases', fontsize=16, **hfont)
    plt.xlabel('Date', fontsize=16, **hfont)

    xs = []
    ys = []
    dates = []
    lastUpdate = ""

    today = datetime.date.today()
    end_date = today
    start_date = datetime.date(2020, 2, 27)
    delta = datetime.timedelta(days=1)
    i = 0
    while start_date < end_date:
        url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/"+start_date.strftime("%m-%d-%Y")+".csv"
        data = pd.read_csv(url)
        df = pd.DataFrame(data)
        selectCountry = df.loc[df['Country/Region'] == country]
        if len(selectCountry["Last Update"].values) is not 1:
            if country == "UK":
                selectCountry = df.loc[(df['Country/Region'] == "United Kingdom") & ((df['Province/State'] == "") | (df['Province/State'] == "UK"))]
            elif country == "United Kingdom":
                selectCountry = df.loc[(df['Country/Region'] == "UK") & ((df['Province/State']) == "" | (df['Province/State'] == "UK"))]
        if len(selectCountry["Last Update"].values) is 1:
            if selectCountry["Last Update"].values[0] > lastUpdate:
                lastUpdate = selectCountry["Last Update"].values[0]
        dates.append(start_date.strftime("%d-%m"))
        xs.append(i)
        if len(selectCountry["Confirmed"].values) is 1:
            ys.append(selectCountry["Confirmed"].values[0])
        else:
            if len(ys) > 0:
                ys.append(ys[-1])
            else:
                ys.append(0)
        i = i + 1
        start_date += delta


    y_pos = np.arange(len(dates))
    new_x = np.array(xs)
    new_y = np.array(ys)

    A = lsr(new_x, new_y)

    linsp = np.linspace(min(xs), max(xs) + 5.5, 10000)
    gr = A[0] + A[1] * 1.4**linsp
    plt.plot(linsp, gr, 'b-', label = "Regression")

    futureDates = []
    pred = []
    for k in range(5):
        dates.append(start_date.strftime("%d-%m"))
        futureDates.append(i)
        pred.append(A[0] + A[1] * 1.4**i)
        xs.append(i)
        i = i + 1
        start_date += delta
    plt.plot(new_x, new_y, 'r.', label = "Current cases")
    plt.plot(futureDates, pred, 'rX', label = "Predicted cases")

    plt.title('Prediction of cases ('+ country +') - Last Timestamp: ' + lastUpdate, fontsize=20, **hfont)
    plt.xticks(xs, dates, rotation='vertical')
    plt.legend(loc="upper left")

    mpld3.save_html(f1, "./templates/" + country + ".html")
    plt.close()
    return

def getCountries():
    today = datetime.date.today() - datetime.timedelta(days=1)
    url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/"+today.strftime("%m-%d-%Y")+".csv"
    data = pd.read_csv(url)
    df = pd.DataFrame(data)
    countries = df['Country/Region'].tolist()
    ret = set()
    for c in countries:
        c = re.sub(r"\s+", '-', c)
        ret.add(c)
    return ret

@app.route("/")
def home():
    countries = getCountries()
    return render_template('home.html', options=countries)

@app.route("/<country>")
def cntry(country):
    freedom = escape(country)
    freedom = re.sub(r"-", " ", freedom)
    print(freedom)
    graphMeBabyOneMoreTime(freedom)
    return render_template(freedom + '.html')