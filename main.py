from flask import Flask #Web application requirement
from flask import request #Web application requirement
from io import BytesIO #NEW Web application requirement
import base64 #NEW Web application requirement

import urllib.request, urllib.parse, urllib.error
import xml.etree.ElementTree as ET
import datetime
from matplotlib.figure import Figure #Web application requiremnt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

app = Flask(__name__) #Web application requirement

#Web application requirement
@app.route("/")
def index():
    station = request.args.get("station", "")
    if station:
        observation = observation_from(station)
        forecast = forecast_from(station)
    else:
        observation = ""
        forecast = ""
    return (
        """<form action="" method="get">
                Enter a weather station: <input type="text" name = "station">
                <input type="submit" value="Get Observation">
              </form>""" + "Current Observation: " + observation
              + "<br />" + "Forecast: " + forecast)

def observation_from(station):
    """Get current observation for given station."""
    try:
        station = station.upper()
        data = urllib.request.urlopen('https://w1.weather.gov/xml/current_obs/' + station + '.xml')
    except:
        return "invalid input"

    #Parse the XML for the current observation
    tree = ET.parse(data)
    root = tree.getroot()

    global location
    location = root.find('location').text
    dtg_str = root.find('observation_time_rfc822').text
    global dtg_obj
    dtg_obj = datetime.datetime.strptime(dtg_str, '%a, %d %b %Y %H:%M:%S %z')
    dtg_obj_clean = dtg_obj.strftime('%B %d, %Y %H:%M')
    weather = root.find('weather').text
    global t
    t = float(root.find('temp_f').text)
    global td
    td = float(root.find('dewpoint_f').text)
    global ws
    ws = float(root.find('wind_kt').text)
    wd = root.find('wind_dir').text
    global lat
    lat = root.find('latitude').text
    global lon
    lon = root.find('longitude').text

    #Convert the data into a Series
    return ("<br />" + location + "<br />" +
    dtg_obj_clean + "<br />" +
    'Weather: ' + weather + "<br />" +
    'Temperature (F): ' + str(t) + "<br />" +
    'Dew Point (F): ' + str(td) + "<br />" +
    'Wind Speed (kts): ' + str(ws) +"<br />" +
    'Wind Direction: ' + wd + "<br />" +
    'Latitude: ' + lat + "<br />" +
    'Longitude: ' + lon)
    #obj = pd.Series([location, dtg_obj_clean, weather, t, td, ws, wd, lat, lon], index=['Location', 'DTG', 'Weather', 'Temperature', 'Dew Point', 'Wind Speed', 'Wind Direction', 'Latitude', 'Longitude'])
    #return str(obj)

def forecast_from(station):

    dtg_list = list()
    dtg_day = list()
    dtg_hour = list()
    temp_list = list()
    td_list = list()
    wind_list = list()
    wind_gust_list = list()
    wind_dir_list = list()
    u_comp = list()
    v_comp = list()
    prob_precip = list()
    cloud_cover = list()
    qpf = list()

    #Get forecast XML for station
    data2 = urllib.request.urlopen('https://forecast.weather.gov/MapClick.php?lat=' + lat + '&lon=' + lon + '&FcstType=digitalDWML')
    tree2 = ET.parse(data2)
    root2 = tree2.getroot()

    #Parse the XML into lists
    t1 = root2.findall('data/time-layout/start-valid-time')

    #Clean up the DTG using datetime object
    for child in t1:
        date_time_str = child.text
        date_time_obj = datetime.datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M:%S%z')
        dtg_list.append(date_time_obj)

    t2 = root2.findall('data/parameters/temperature')

    for child in t2:
        if child.get('type') == 'hourly':
            t3 = child.findall('value')
            for child in t3:
                if child.text != None:
                    temp_list.append(float(child.text)) #Make a list of Temperatures
                else:
                    temp_list.append(float('nan'))
        elif child.get('type') == 'dew point':
            t4 = child.findall('value')
            for child in t4:
                if child.text != None:
                    td_list.append(float(child.text)) #Make a list of Dew Points
                else:
                    td_list.append(float('nan'))

    w2 = root2.findall('data/parameters/wind-speed')

    for child in w2:
        if child.get('type') == 'sustained':
            w3 = child.findall('value')
            for child in w3:
                if child.text != None:
                    wind_list.append(float(child.text)* 0.868976) #Convert Sustained to kts
                else:
                    wind_list.append(float('nan'))
        elif child.get('type') == 'gust':
            w4 = child.findall('value')
            for child in w4:
                if child.text != None:
                    wind_gust_list.append(float(child.text)* 0.868976) #Convert Gusts to kts
                else:
                    wind_gust_list.append(float('nan'))

    d2 = root2.findall('data/parameters/direction')

    for child in d2:
        t3 = child.findall('value')
        for child in t3:
            if child.text != None:
                wind_dir_list.append(float(child.text))#Make a list of wind directions (deg)
            else:
                wind_dir_list.append(float('nan'))

    e2 = root2.findall('data/parameters/probability-of-precipitation')

    for child in e2:
        t3 = child.findall('value')
        for child in t3:
            if child.text != None:
                prob_precip.append(float(child.text)) #Make a list of PoPs (%)
            else:
                prob_precip.append(float('nan'))

    e2 = root2.findall('data/parameters/cloud-amount')

    for child in e2:
        t3 = child.findall('value')
        for child in t3:
            if child.text != None:
                cloud_cover.append(float(child.text)) #Make a list of sky cover (%)
            else:
                cloud_cover.append(float('nan'))

    e2 = root2.findall('data/parameters/hourly-qpf')

    for child in e2:
        t3 = child.findall('value')
        for child in t3:
            if child.text != None:
                qpf.append(float(child.text)) #Make a list of QPF (%)
            else:
                qpf.append(0.0) # Need to make this one zero instead of NaN for the dailyQPF summation to work

    #Make a dataframe of all the lists above
    data = {
    'DTG': dtg_list,
    'Temperature': temp_list,
    'Dew Point': td_list,
    'Wind Speed': wind_list,
    'Gusts': wind_gust_list,
    'Direction': wind_dir_list,
    'PoP': prob_precip,
    'Sky Cover': cloud_cover,
    'QPF': qpf}
    frame = pd.DataFrame(data)

    #Break wind speed and direction into U and V comp for barbs (remember math 0deg != compass 0deg)
    for i in range(0, len(frame.index)):
        frame.at[i, 'u_comp'] = round(-1*float(wind_list[i])*(np.sin(float(wind_dir_list[i])*(np.pi/180))), 2)
        frame.at[i, 'v_comp'] = round(-1*float(wind_list[i])*(np.cos(float(wind_dir_list[i])*(np.pi/180))), 2)
        #Add two colums for daily High and Low Temps to prepare for below steps
        frame.at[i, 'hiTemps'] = None
        frame.at[i, 'loTemps'] = None
        frame.at[i, 'dailyQPF'] = None

    #Set frame index to DTG
    frame = frame.set_index(['DTG'])

    #Find daily high and low temp
    hiTemp = -100 #arbitrarily low
    loTemp = 100 #arbitrarily high
    dailyPrecip = 0
    dayCheck = frame.index[0].weekday()
    curDay = frame.index[0].weekday()
    hiTempIndex = -1
    lowTempIndex = -1
    for i in range(0, len(frame.index)):
        curTemp = frame['Temperature'][i]
        if curDay == dayCheck: #"For a given day..."
            curDay = frame.index[i].weekday()
            dailyPrecip += frame['QPF'][i]
            try:
                dayCheck = frame.index[i+1].weekday()
            except: #last iteration through entire data frame
                frame['hiTemps'][hiTempIndex] = hiTemp
                frame['loTemps'][loTempIndex] = loTemp
                frame['dailyQPF'][i] = dailyPrecip
                break
            if curTemp > hiTemp:
                hiTemp = curTemp
                hiTempIndex = i
            if curTemp < loTemp:
                loTemp = curTemp
                loTempIndex = i
            else:
                continue
        else: #last hour of day
            #add hiTempIndex and lowTempIndex to DataFrame before overwriting
            frame['hiTemps'][hiTempIndex] = hiTemp
            frame['loTemps'][loTempIndex] = loTemp
            frame['dailyQPF'][i] = dailyPrecip
            hiTemp = -100
            loTemp = 100
            dailyPrecip = 0
            curDay = frame.index[i].weekday()
    #pd.set_option('display.max_rows', None) #This will print the entire DataFrame
    #print (frame)

    fig = Figure(figsize=(16,8))
    axes = fig.subplots(3, sharex=True)#, figsize=(16, 8))
    axes[0].plot(dtg_obj, t, 'or', color='red')
    axes[0].plot(dtg_obj, td, 'or', color='green')
    axes[0].plot(frame.index, frame['Temperature'], label='Ambient', c='red')
    axes[0].plot(frame.index, frame['Dew Point'], label='Dew Pt.', c='green')
    #Add high and low temp annotations
    for i, value in enumerate(frame['hiTemps']):
        if pd.notnull(frame['hiTemps'][i]):
            axes[0].plot(frame.index[i], frame['Temperature'][i], marker='.', color='black')
            axes[0].annotate(int(value), (frame.index[i], frame['Temperature'][i]), ha='center')
    for i, value in enumerate(frame['loTemps']):
        if pd.notnull(frame['loTemps'][i]):
            axes[0].plot(frame.index[i], frame['Temperature'][i], marker='.', color='black')
            axes[0].annotate(int(value), (frame.index[i], frame['Temperature'][i]), ha='center', va='top')
    #Plot from dataframe
    axes[1].plot(dtg_obj, ws, 'or', color='blue')
    axes[1].plot(frame.index, frame['Wind Speed'], label='Wind', c='blue')
    axes[1].plot(frame.index, frame['Gusts'], label='Gust', c='DarkBlue')
    axes[1].barbs(frame.index[::6], frame['Wind Speed'][::6], frame['u_comp'][::6], frame['v_comp'][::6], pivot='middle', length = 6)
    axes[2].plot(frame.index, frame['PoP'], label='Precip %', c='DarkGreen')
    axes[2].plot(frame.index, frame['Sky Cover'], label='Sky Cover', c='grey')
    QPFaxes = axes[2].twinx()
    QPFaxes.bar(frame.index, frame['QPF'], width=0.03, alpha=0.35, label='QPF', color='green')

    #Display precip annotations by event (resets when the rain stops)
    counter = 0
    qpfCounter = 0
    for i, value in enumerate(frame['QPF']):
        if value != 0: #It's raining
            qpfCounter += value
            counter += 1
            if i == len(frame.index) - 1: #last cycle and it has been raining
                axes[2].annotate(round(qpfCounter, 2), (frame.index[i - int(counter/2)], 0.2), ha='center', va='center', xycoords = ('data', 'axes fraction'),
                bbox=dict(pad=3, facecolor='white', alpha=1, edgecolor='darkGreen', linewidth=1)) #plot a box on the right

        elif qpfCounter != 0: #It just stopped raining
            axes[2].annotate(round(qpfCounter, 2), (frame.index[i - int(counter/2)], 0.2), ha='center', va='center', xycoords = ('data', 'axes fraction'),
            bbox=dict(pad=3, facecolor='white', alpha=1, edgecolor='darkGreen', linewidth=1)) #plot a box on the right
            qpfCounter = 0 #reset
            counter = 0 #reset

        else: #It hasn't rained in the last hour
            continue

    #Format the subplots
    axes[0].legend(loc='upper right')
    axes[0].grid(True, linestyle = 'dotted')
    axes[1].legend(loc='upper right')
    axes[1].grid(True, linestyle = 'dotted')
    axes[2].legend(loc='upper right')
    axes[2].grid(True, linestyle = 'dotted')

    axes[0].set(ylabel='Temperature (F)')
    axes[1].set(ylabel='Wind (kts)')
    axes[2].set(ylabel='Percent')
    QPFaxes.set(ylabel='Inches')
    axes[2].set(xlabel='Date')
    axes[2].set_ylim([0,100])
    QPFaxes.set_ylim(bottom=0)
    myFmt = mdates.DateFormatter('%A')# %H:%M %z')
    axes[2].xaxis.set_major_formatter(myFmt)
    fig.autofmt_xdate()

    fig.suptitle(location)

    #Save it to a temporary buffer.
    buf = BytesIO()
    fig.savefig(buf, format='png')
    #Embed the result in the html output.
    data = base64.b64encode(buf.getbuffer()).decode('ascii')
    return f"<img src='data:image/png;base64,{data}'/>"

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
