import geocoder
import pycountry
from pycountry_convert import country_alpha2_to_continent_code, convert_continent_code_to_continent_name


def reverse_geocode(lat, lng):
    reverse_data = geocoder.osm_reverse.OsmReverse((lat, lng)).geojson
    country = None
    city = None
    continent = None

    try:
        feature_properties = reverse_data["features"][0]["properties"]
        cc = feature_properties["country_code"].upper()
        city = None
        if "city" in feature_properties:
            city = feature_properties["city"]
        elif "town" in feature_properties:
            city = feature_properties["town"]
        elif "state" in feature_properties:
            city = feature_properties["state"]
        elif "county" in feature_properties:
            city = feature_properties["county"]

        country = pycountry.countries.get(alpha_2=cc).name
        continent_code = country_alpha2_to_continent_code(cc)
        continent = convert_continent_code_to_continent_name(continent_code)
    except:
        return None, None, None
    else:
        return continent, country, city
