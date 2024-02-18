import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import pandas as pd
from shapely.geometry import Polygon
import geopandas as gpd
import matplotlib.pyplot as plt
import requests
from requests.adapters import HTTPAdapter, Retry
from bs4 import BeautifulSoup
from io import StringIO


def get_content_url(page_url: str):
    """A function that retrieves the content of a page."""
    s = requests.Session()
    retries = Retry(total=5,
                    backoff_factor=0.1,
                    status_forcelist=[500, 502, 503, 504, 104])
    s.mount('http://', HTTPAdapter(max_retries=retries))
    page = s.get(page_url)
    return BeautifulSoup(page.content, "html.parser")


def get_data_from_table(page_content, converters: dict = None) -> pd.DataFrame:
    """
    A function that retrieves data from tables containing cost-of-living information.
    """
    table = page_content.find('table', class_='data_wide_table')
    cost_df = pd.read_html(StringIO(str(table)), converters=converters)[0]
    return cost_df


def convert_euro_eurocent(price: str) -> int:
    """
    Function used to clean data and standardize the price format.
    """
    cleared_with_leading_zeros = price.replace(
        '.', '').replace(',', '').rstrip('€').strip()
    cleared = cleared_with_leading_zeros.lstrip('0') if not set(
        cleared_with_leading_zeros) == {'0'} else '0'
    try:
        return int(cleared)
    except ValueError:
        print(
            f'Cannot parse value "{price}" as price ("{cleared}" after clearing). Defaulting to <NA>...', file=sys.stderr)
        return pd.NA


def convert_type_avg_price(df: pd.DataFrame) -> pd.DataFrame:
    """
    Function used to clean avarage price data.
    """
    df_2 = df.copy()
    for i in range(len(df_2)):
        if df_2.loc[i, "Avg_price"] == 'Edit':
            pass
        elif df_2.loc[i, "Avg_price"] == '?':
            df_2.loc[i, "Avg_price"] = pd.NA
        else:
            parsed_price = convert_euro_eurocent(df_2.loc[i].Avg_price)
            df_2.loc[i, "Avg_price"] = parsed_price
    return df_2


def separate_types(country_city_dict:dict, country: str, city: str, item: str) -> dict[str, pd.DataFrame]:
    """
    The function used to separation categories.
    """
    df = country_city_dict[country][city]
    df = convert_type_avg_price(df)
    key_type = df.loc[df['Avg_price'] == 'Edit'].Type
    dict_df = {}
    if item == 'Restaurants':
        next_item = key_type.iloc[0]
        end_id = df.loc[df['Type'] == next_item].index.item()-1
        df = df.iloc[0:end_id]
        df['Type'] = df.Type.str.strip().str.replace(' ', '')
        df = df.astype({'Avg_price': pd.Int64Dtype()})
        dict_df[item] = df
    for x in range(len(key_type)):
        name = key_type.iloc[x]
        if name == item:
            start_id = df.loc[df['Type'] == name].index.item()+1
            if item == key_type.iloc[-1]:
                df = df.iloc[start_id::]
            else:
                next_item = key_type.iloc[x+1]
                end_id = df.loc[df['Type'] == next_item].index.item()
                df = df.iloc[start_id:end_id]
            df['Type'] = df.Type.str.strip().str.replace(' ', '')
            df = df.astype({'Avg_price': pd.Int64Dtype()})
            dict_df[item] = df
    return dict_df


def prepare_df( country: str, city: str, item: str,  country_city_df: pd.DataFrame, country_city_dict: dict[str, pd.DataFrame], categories:pd.DataFrame) -> pd.DataFrame:
    """
    The function used to prepared cleaned Dataframe for specific country, city and category.
    """
    dict_type = separate_types(country_city_dict, country, city, item)
    separate_types_df = dict_type[item].set_index('Type')
    df_t = separate_types_df['Avg_price'].to_frame().T.reset_index()
    df_t.insert(loc=1, column='city_id', value=country_city_df.loc[(
        country_city_df['country'] == country) & (country_city_df['city'] == city)].index.item())
    if item != 'Restaurants':
        df_t.insert(loc=2, column='category_id',
                    value=categories.loc[categories['name'] == item].index.item())
    else:
        df_t.insert(loc=2, column='category_id', value=0)
    return df_t.iloc[:, 1:].set_index('city_id')


def make_bbox(long0: float, lat0: float, long1: float, lat1: float) -> Polygon:
    """
    The function used to prepare box for map.
    """

    return Polygon([[long0, lat0],
                    [long1, lat0],
                    [long1, lat1],
                    [long0, lat1]])


def create_europe_map(df: pd.DataFrame, attributes: list[str], attribute_label: str, cmap:str,size=10, size_2=5):
    """
    The function used to create Europe map with specific values and dots.
    """

    bbox = make_bbox(-36.210938, 28.304381, 197.226563, 81.361287)
    bbox_gdf = gpd.GeoDataFrame(index=[0], crs='epsg:4326', geometry=[bbox])
    worldmap = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
    europe = worldmap[(worldmap.continent == 'Europe')
                      & (worldmap.name != 'Russia')]
    europe = europe.overlay(bbox_gdf, how="intersection")
    fig, ax = plt.subplots(figsize=(30, 10))
    europe.plot(color="lightgrey", edgecolor="black", ax=ax)
    x = df['lng']
    y = df['lat']
    z = df[attributes[0]]
    plt.scatter(x, y, s=z/size, c=z, alpha=0.5,
                cmap=cmap)
    if len(attributes)>1:
        d = df[attributes[1]]
        plt.scatter(x, y, s=z/size_2, c=z, alpha=0.5,
                cmap=cmap)
    plt.colorbar(label=attribute_label)
