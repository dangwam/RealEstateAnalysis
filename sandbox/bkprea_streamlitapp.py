import data_extract as de
import streamlit as st
import plotly.express as px
#import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objs as go
import folium
from folium.plugins import MarkerCluster
from folium.plugins import HeatMap
from streamlit_folium import folium_static
from folium.plugins import MiniMap
from folium.plugins import Fullscreen
import os
import warnings
warnings.filterwarnings('ignore')

filtered_df = pd.DataFrame()

st.set_page_config(page_title="RealEstateAnalytics!!!", page_icon=":bar_chart:",layout="wide")
st.title(" :bar_chart: RealEstate Analytics dashboard EDA")
st.markdown('<style>div.block-container{padding-top:2rem;}</style>',unsafe_allow_html=True)

base_dir = r"B:\workspace\apps\RealEstateAnalysis\datare"
#fname = "B:\workspace\\apps\RealEstateAnalysis\\rapidapi_data.json"
def process_data(params,fname):
    if os.path.exists(fname):
        loaded_data = de.load_json(filename=fname)
    else:
         loaded_data = de.fetch_data(params,fname)
    if not loaded_data:
        print("Failed to load data for analysis.")
    else:
        de.get_json_info(loaded_data)

    if loaded_data and 'searchResults' in loaded_data:
        properties = [item['property'] for item in loaded_data['searchResults'] if 'property' in item]

    # Extract relevant information
    extracted_data = []

    for prop in properties:
        #print(prop)
        zipid = prop.get('zpid', '')
        image = prop['media']['propertyPhotoLinks']['mediumSizeLink']
        if 'location' in prop:
            latitude = prop['location']['latitude']
            longitude = prop['location']['longitude']
        else :
            latitude = 0
            longitude = 0
        lot_size_acres = prop.get('lotSizeWithUnit', {}).get('lotSize', '')
        lot_size_unit = prop.get('lotSizeWithUnit', {}).get('lotSizeUnit', '')
        lot_size_sqft = ''
        if lot_size_acres and lot_size_unit.lower() == 'acres':
                lot_size_sqft = float(lot_size_acres) * 43560  # Convert acres to square feet
        last_sold_date = prop.get('lastSoldDate', '')
        ######################################################
        extracted_data.append({
                'zipid' : zipid,
                'Address': prop['address'].get('streetAddress', ''),
                'Image' : image,
                'Latitude' : latitude,
                'Longitude' : longitude,
                'City': prop['address'].get('city', ''),
                'State': prop['address'].get('state', ''),
                'Zip': prop['address'].get('zipcode', ''),
                'Price': prop['price'].get('value', '') if 'price' in prop else '',
                'SqFtPrc': str(prop['price'].get('pricePerSquareFoot', '')) if 'price' in prop else '',
                'RentEst': prop['estimates'].get('rentZestimate', '') if 'estimates' in prop else '',
                'Bedrooms': prop.get('bedrooms', ''),
                'Bathrooms': prop.get('bathrooms', ''),
                'Living Area': str(prop.get('livingArea', '')),
                'Lot Size (Acres)': str(lot_size_acres),
                'Lot Size (Sqft)': str(lot_size_sqft),  # Add calculated field
                'Year Built': str(prop.get('yearBuilt', '')),
                #'Year Built': pd.to_numeric(prop.get('yearBuilt', pd.NA), errors='coerce'),
                'Days on Zillow': prop.get('daysOnZillow', ''),
                'isPreforeclosureAuction' : prop.get('isPreforeclosureAuction',''),
                'Zestimate': prop['estimates'].get('zestimate', '') if 'estimates' in prop else '',
                'Rent Zestimate': prop['estimates'].get('rentZestimate', '') if 'estimates' in prop else '',
                'Last Sold Date': last_sold_date,
                'Property Type': prop.get('propertyType', ''),
                'Listing Status': prop['listing'].get('listingStatus', '') if 'listing' in prop else ''

        })
    prop_df = pd.DataFrame(extracted_data)
    # Convert image URLs to HTML
    #prop_df['Property'] = prop_df['Image'].apply(image_to_html)
    columns_to_select = ['Image', 'Address', 'City', 'Zip', 'Latitude', 'Longitude', 'Property Type','Year Built','Lot Size (Acres)','Living Area','Price','SqFtPrc','State']
    prop_df = prop_df[columns_to_select]
       
    return prop_df

main_df = pd.DataFrame()

st.sidebar.header("Search & Fetch Data")
with st.sidebar:
    state = st.sidebar.multiselect("State", de.list_of_states)
    fname = os.path.join(base_dir, f"{state}_rapidapi_data.json")
    # Query parameters
    params = {
        "location": state,
        #"page": "1",
        "sortOrder": "Newest",
        #"listingStatus": "Sold"
        "listingStatus": "For_Sale"
            }
    df = process_data(params,fname)
    ##
    if not state:
        df2 = df.copy()
    else:
        df2 = df[df["State"] == state]
    # Create for State
    city_list = list(df2["City"].unique())
    city = st.sidebar.multiselect("City", city_list)
    if not city:
        df3 = df2.copy()
    else:
        df3 = df2[df2["City"].isin(city)]
    # Create for City
    zip_list = list(df3["Zip"].unique())
    zip = st.sidebar.multiselect("Zip",zip_list)

    # Filter the data based on Region, State and City
    # Filter the data based on Region, State and City
    
    if not state and not city and not zip:
        filtered_df = df
    elif not city and not zip:
        filtered_df = df[df["state"] == state]
    elif not state and not zip:
        filtered_df = df[df["city"].isin(city)]
    elif city and zip:
        filtered_df = df3[df["city"].isin(city) & df3["zip"].isin(zip)]
    elif state and zip:
        filtered_df = df3[df["state"].isin(state) & df3["zip"].isin(zip)]
    elif state and city:
        filtered_df = df3[df["state"].isin(state) & df3["city"].isin(city)]
    elif zip:
        filtered_df = df3[df3["zip"].isin(zip)]
    else:
        filtered_df = df3[df3["state"].isin(state) & df3["city"].isin(city) & df3["zip"].isin(zip)]

# Create a base map centered on the mean coordinates of your data
m = folium.Map(location=[filtered_df['Latitude'].mean(), filtered_df['Longitude'].mean()], zoom_start=6)
    
r1c1, r1c2 = st.columns([4, 1])

with r1c1:
    #df_styled = filtered_df.style.background_gradient()
    #df_styled = style_dataframe(filtered_df)
    #filtered_df = filtered_df.style.set_table_styles(styles)
    #st.metric(label="50 day AvgPrice", value=50)
    # Group by Property Type and calculate average Price
    st.dataframe(filtered_df, column_config={"Image": st.column_config.ImageColumn(label="Property", width = "small")}, hide_index=True)
       

with r1c2:
    avg_prices_by_type = filtered_df.groupby('Property Type')['Price'].mean().reset_index()
    
    # Sort by average price in descending order
    avg_prices_by_type = avg_prices_by_type.sort_values('Price', ascending=False)

    # Format the average price as currency
    avg_prices_by_type['AveragePrice'] = avg_prices_by_type['Price'].apply(lambda x: f"${x:,.2f}")
    
    # Create the bar chart
    fig = px.bar(
        avg_prices_by_type,
        x='Property Type',
        y='Price',
        title='Average Prices by Property Type',
        labels={'Price': 'Average Price'},
        text_auto='.2s'  # Display price values on bars
    )

    # Customize the layout
    fig.update_layout(
        xaxis_title='Property Type',
        yaxis_title='Average Price ($)',
        yaxis_tickformat='$,.0f'
    )

    # Display the chart in Streamlit
    st.plotly_chart(fig, use_container_width=True)

##############################################################################

r2c1, r2c2 = st.columns([1,1])

with r2c1:
    # Add markers for each city
    for idx, row in filtered_df.iterrows():
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=1,
            popup=f"{row['City']}: ${row['Price']:,.0f}",
            color="red",
            fill=True,
            fillColor="red"
        ).add_to(m)
    
    marker_cluster = MarkerCluster().add_to(m)
    for idx, row in filtered_df.iterrows():
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=f"{row['City']}: ${row['Price']:,.0f}",
        ).add_to(marker_cluster)
        
    #folium.LayerControl().add_to(m)
    #MiniMap().add_to(m)
    Fullscreen().add_to(m)



    # Display the map in Streamlit
    st.title("Real Estate Prices by City")
    folium_static(m)

with r2c2:

    heat_data = [[row['Latitude'], row['Longitude'], row['Price']] for idx, row in filtered_df.iterrows()]
    HeatMap(heat_data).add_to(m)
    st.title("Prices heatMap")
    folium_static(m)

