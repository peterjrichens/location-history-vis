import json
import pandas as pd
import datetime
from shapely.geometry import Point, shape

def gps_to_country(longitude, latitude, geo_json):
    point = Point(longitude, latitude)

    for record in geo_json['features']:
        polygon = shape(record['geometry'])
        if polygon.contains(point):
            return record['properties']['name']
    return 'other'

def get_countries(df, geojson_name, granularity=2):
    # create low granularity groups and look up countries
    # would be very slow and unnecessary to do this for every record
    df['lat_round'] = df.lat.apply(lambda x: round(x, granularity))
    df['lon_round'] = df.lon.apply(lambda x: round(x, granularity))
    groups = pd.concat([df['lat_round'], df['lon_round']], axis=1).drop_duplicates()
    with open('geojson/%s' % geojson_name) as data_file:
        geo_json = json.load(data_file)
    groups['country'] = groups.apply(lambda row: gps_to_country(row['lon_round'], row['lat_round'], geo_json), axis=1)
    df = df.merge(groups, how='left', on=['lat_round', 'lon_round'])
    df.drop('lon_round', axis=1, inplace=True)
    df.drop('lat_round', axis=1, inplace=True)
    df = df[df.country!='other']
    return df

def sample(df, frac, granularity=3):
    # sample data within granular groups
    df['lat_round'] = df.lat.apply(lambda x: round(x, granularity))
    df['lon_round'] = df.lon.apply(lambda x: round(x, granularity))
    df_sample = pd.DataFrame()
    max_records = len(df)/100 # ensure no more than 1% of records from any single location
    print "Sampling location groups.."
    for _, location in df.groupby(['lat_round', 'lon_round']):
        if len(location) < 10:
            sample = location #keep all of small groups
        else:
            sample = location.sample(n=min(max_records, int(len(location)*frac)))
        df_sample = pd.concat([df_sample, sample])
    return df_sample

def clean_location_data(sample_frac=0.05):
    with open('LocationHistory.json') as data_file:
        locations = json.load(data_file)['locations']
    df = pd.DataFrame.from_dict(locations)
    print "Raw data as %d records." % len(df)
    # convert to regular gps coordinates
    df['lat'] = df.latitudeE7/1e7
    df['lon'] = df.longitudeE7/1e7

    # convert timestamp to human readable form
    df['time'] = df.timestampMs.apply(
        lambda x: datetime.datetime.fromtimestamp(float(x)/1000).strftime('%Y-%m-%d %H:%M:%S'))


    df = get_countries(df, 'ne_50m_admin_0_countries.geojson')

    df_sample = sample(df, sample_frac)[['time','lat','lon','country']]

    final_json = df_sample.to_json(orient='records')
    with open('location_sample.json', 'w') as outfile:
        json.dump(final_json, outfile)

if __name__ == "__main__":
    clean_location_data(sample_frac=0.05)