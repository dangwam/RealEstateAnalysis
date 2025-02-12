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

st.set_page_config(page_title="RealEstateAnalytics!!!", page_icon=":bar_chart:",layout="wide")
st.title(" :bar_chart: RealEstate Analytics dashboard EDA")
st.markdown('<style>div.block-container{padding-top:1.75rem;}</style>',unsafe_allow_html=True)

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
    columns_to_select = ['Image', 'Address', 'City', 'Property Type', 'Price','SqFtPrc',  'Year Built','Lot Size (Acres)','Living Area','Zip', 'Latitude', 'Longitude','State']
    prop_df = prop_df[columns_to_select]
       
    return prop_df

print("---------------------------------------------------------------------------------------------------------------->>> Start")
base_dir = r"B:\workspace\apps\RealEstateAnalysis\datare"
state_list = de.list_of_states
state = st.sidebar.selectbox("State", options= state_list,placeholder = 'VA')
fname = os.path.join(base_dir, f"{state}_rapidapi_data.json")

    # Query parameters
params = {
        "location": state,
        #"page": "1",
        "sortOrder": "Newest",
        #"listingStatus": "Sold"
        "listingStatus": "For_Sale"
            }
#df = process_data(params,fname)
df = process_data(params,fname)
print(df.head(2))

### df2 is state
if state:
    df_state = df.copy()
else:
    st.write(" You need to select a state to proceed")

# Create for City
city_list = df_state['City'].unique()

city = st.sidebar.multiselect("City", options = city_list)
if not city:
    df_city = df_state.copy()   
else:
    df_city = df_state[df_state["City"].isin(city)]

# Create for Zip
zip_list = df_city['Zip'].unique()
zip = st.sidebar.multiselect("Zip", options = zip_list)
print(zip)
if not zip:
    df_zip = df_city.copy()   
else:
    df_zip = df_city[df_city["Zip"].isin(zip)]

if state and city and zip:
    df_filtered = df_zip
elif  (state and city) and not zip:
    df_filtered = df_city
elif  (state and zip) and not city:
    df_filtered = df_zip
elif (not city and not zip) and state:
    df_filtered = df_state
else:
    df_filtered = df


with st.sidebar:
    avg_prices_by_type = df_filtered.groupby('Property Type')['Price'].mean().reset_index()
    
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

# Create a base map centered on the mean coordinates of your data
m = folium.Map(location=[df_filtered['Latitude'].mean(), df_filtered['Longitude'].mean()], zoom_start=6)


with st.container():
    r1c1, r1c2, r1c3 = st.columns([1, 3.5, 3.5])
    with r1c1:
        #st.header("Coming")
        prefix = "marketdata"
        rc_base_dir = r"B:\workspace\apps\RealEstateAnalysis\datare"
        rc_fname = os.path.join(base_dir, f"rentcatapi_{prefix}_data.json")
        
        
        if os.path.exists(fname):
            rc_loaded_data = de.rc_load_json(filename=rc_fname)
        else:
            rc_loaded_data = de.rc_fetch_data(fname=rc_fname)

        data = rc_loaded_data
        # 1️⃣ Extracting Aggregate Data (Now Includes SaleData Metrics)
        
        df_aggregate = pd.DataFrame([{
            "id": data["id"],
            "zipCode": data["zipCode"],
            "lastUpdatedDate": data["saleData"]["lastUpdatedDate"],
            "averagePrice": data["saleData"]["averagePrice"],
            "medianPrice": data["saleData"]["medianPrice"],
            "minPrice": data["saleData"]["minPrice"],
            "maxPrice": data["saleData"]["maxPrice"],
            "averagePricePerSquareFoot": data["saleData"]["averagePricePerSquareFoot"],
            "medianPricePerSquareFoot": data["saleData"]["medianPricePerSquareFoot"],
            "minPricePerSquareFoot": data["saleData"]["minPricePerSquareFoot"],
            "maxPricePerSquareFoot": data["saleData"]["maxPricePerSquareFoot"],
            "averageSquareFootage": data["saleData"]["averageSquareFootage"],
            "medianSquareFootage": data["saleData"]["medianSquareFootage"],
            "minSquareFootage": data["saleData"]["minSquareFootage"],
            "maxSquareFootage": data["saleData"]["maxSquareFootage"],
            "averageDaysOnMarket": data["saleData"]["averageDaysOnMarket"],
            "medianDaysOnMarket": data["saleData"]["medianDaysOnMarket"],
            "minDaysOnMarket": data["saleData"]["minDaysOnMarket"],
            "maxDaysOnMarket": data["saleData"]["maxDaysOnMarket"],
            "newListings": data["saleData"]["newListings"],
            "totalListings": data["saleData"]["totalListings"]
        }])
        
        # 2️⃣ Extracting Property Type Data
        property_rows = []

        # Add the latest saleData first
        last_updated = data["saleData"]["lastUpdatedDate"][:10]  # Extract YYYY-MM-DD
        for item in data["saleData"]["dataByPropertyType"]:
            item["date"] = last_updated
            property_rows.append(item)

        # Add historical property data
        for date, history_data in data["saleData"]["history"].items():
            for item in history_data["dataByPropertyType"]:
                item["date"] = history_data["date"][:10]  # Extract YYYY-MM-DD
                property_rows.append(item)

        # Convert to DataFrame
        df_property_types = pd.DataFrame(property_rows)

        # Convert `date` column to datetime format and sort by date (latest first)
        df_property_types["date"] = pd.to_datetime(df_property_types["date"])
        df_property_types = df_property_types.sort_values(by="date", ascending=False)

        # Reorder columns to make `date` the first column
        df_property_types = df_property_types[['date'] + [col for col in df_property_types.columns if col != 'date']]

        # 3️⃣ Extracting Bedroom Data
        bedroom_rows = []

        # Add the latest saleData first
        for item in data["saleData"]["dataByBedrooms"]:
            item["date"] = last_updated
            bedroom_rows.append(item)

        # Add historical bedroom data
        for date, history_data in data["saleData"]["history"].items():
            for item in history_data["dataByBedrooms"]:
                item["date"] = history_data["date"][:10]  # Extract YYYY-MM-DD
                bedroom_rows.append(item)

        # Convert to DataFrame
        df_bedrooms = pd.DataFrame(bedroom_rows)

        # Convert `date` column to datetime format and sort by date (latest first)
        df_bedrooms["date"] = pd.to_datetime(df_bedrooms["date"])
        df_bedrooms = df_bedrooms.sort_values(by="date", ascending=False)

        # Reorder columns to make `date` the first column
        df_bedrooms = df_bedrooms[['date'] + [col for col in df_bedrooms.columns if col != 'date']]

        ######################Building metrics for the r1c1
        ## using aggregate data from df_aggregare
        
        st.metric("Median 🏡 Price",value = df_aggregate["medianPrice"],delta = "-6%",border=True)
        st.metric("Average 💰 sqft",value = df_aggregate["averagePricePerSquareFoot"],border=True)
        st.metric("Average Days 🏗 market",value = df_aggregate["averageDaysOnMarket"],delta = "5%",border=True)
    
    with r1c2:
        df_out = df_filtered.copy()
        #st.dataframe(df_filtered, column_config={"Image": st.column_config.ImageColumn(label="Property", width = "small")}, hide_index=True,height=400,use_container_width=True)
        # 📌 Rename Columns for Better Readability
        df_out.rename(columns={
            #"Image": "Property 🏡",
            "Address": "Address 📍",
            "City": "City 🏙",
            "Zip": "ZIP Code",
            "Latitude": "Latitude 🌍",
            "Longitude": "Longitude 🌍",
            "Property Type": "Type 🏠",
            "Year Built": "Year Built 🏗",
            "Lot Size (Acres)": "Lot Size (Acres) 🌳",
            "Living Area": "Living Area (sqft) 📏",
            "Price": "Price",
            "SqFtPrc": "Price per SqFt 💲",
            "State": "State 📍"
            }, inplace=True)
        
        # Convert numeric columns from strings to appropriate types
        df_out["Price 💰"] = df_out["Price"].astype(float)
        #df_out["Price per SqFt 💲"] = df_out["Price per SqFt 💲"].astype(float)
        #df_out["Lot Size (Acres) 🌳"] = df_out["Lot Size (Acres) 🌳"].replace({" acres": ""}, regex=True).astype(float)
                
        
        # Apply formatting AFTER conversion
        df_styled = df_out.style.format({
            "Price 💰": "${:,.0f}",  # Format as currency
            #"Price per SqFt 💲": "${:,.2f}/sqft",
            #"Lot Size (Acres) 🌳": "{:.2f} acres"
        }).set_properties(**{
            #"border": "2px solid #1904d4",
            "color": "#0519f7",
            "text-align": "center",
            "font-weight": "bold"
        }).applymap(lambda x: "background-color: #ebfcfc;" if isinstance(x, str) else "background-color:#fcebfc")  

        # ✨ Make Column Headers Bold & Italic
       #df_styled = df_styled.set_table_styles([{"selector": "th", "props": [("font-weight", "bold"), ("font-style", "italic")]}])
        # 🔹 Apply Bold & Italic Styling to Column Names Using Markdown
        #df_out.columns = [f"**_{col}_**" for col in df_out.columns]

        st.dataframe(df_styled, column_config={"Image": st.column_config.ImageColumn(label="Property", width = "small")}, hide_index=True,height=400,use_container_width=True)
    
    
    with r1c3:
    # Create a treem based on State, city, zip
    #st.subheader("Hierarchical view using TreeMap")
        fig3 = px.treemap(df_filtered, path = ["State","City","Zip"], values = "Price",hover_data = ["Price"],color = "Price")
        #fig3.update_layout(width = 800, height = 400)
        fig3.update_layout(height=400, margin=dict(t=0, l=0, r=0, b=0))  # Remove margins
        st.plotly_chart(fig3, use_container_width=True)

r2c1, r2c2 = st.columns([1,1])

with r2c1:
    # Add markers for each city
    for idx, row in df_filtered.iterrows():
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=1,
            popup=f"{row['City']}: ${row['Price']:,.0f}",
            color="red",
            fill=True,
            fillColor="red"
        ).add_to(m)
    
    marker_cluster = MarkerCluster().add_to(m)
    for idx, row in df_filtered.iterrows():
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=f"{row['Address']}: ${row['Price']:,.0f}",
        ).add_to(marker_cluster)
        
    #folium.LayerControl().add_to(m)
    #MiniMap().add_to(m)
    Fullscreen().add_to(m)
    
    # Display the map in Streamlit
    st.subheader("Real Estate Prices by City")
    folium_static(m)
    

with r2c2:
    heat_data = [[row['Latitude'], row['Longitude'], row['Price']] for idx, row in df_filtered.iterrows()]
    HeatMap(heat_data).add_to(m)
    st.subheader("Prices heatMap")
    folium_static(m)
    
r3c1,r3c2, r3c3, r3c4 = st.columns([1,1,1,1])
# Ensure Date Column is in datetime format
df_property_types["date"] = pd.to_datetime(df_property_types["date"])

    # 📌 Sidebar Filter for Property Type
property_types = df_property_types["propertyType"].unique()
selected_types = st.sidebar.multiselect("Select Property Type(s)", property_types, default=property_types)

# Filter Data
df_filtered_prop_data = df_property_types[df_property_types["propertyType"].isin(selected_types)]
print()

with r3c1:
    
    # 🎯 **1️⃣ Line Chart - Price Trend Over Time**
    fig_line = px.line(df_filtered_prop_data, x ="date", y="averagePrice", color="propertyType",
                        title="Property Price Trend Over Time",
                        labels={"averagePrice": "Average Price ($)", "date": "Date"},
                        markers=True)
    st.plotly_chart(fig_line, use_container_width=True)
with r3c2:
    # 🎯 **2️⃣ Bar Chart - Comparing Property Types**
    fig_bar = px.bar(df_filtered_prop_data, x="date", y="averagePrice", color="propertyType",
                    title="Average Price Comparison by Property Type",
                    barmode="group", labels={"averagePrice": "Average Price ($)", "date": "Date"})
    st.plotly_chart(fig_bar, use_container_width=True)

with r3c3:
    # 🎯 **3️⃣ Area Chart - Cumulative Trend**
    fig_area = px.area(df_filtered_prop_data, x="date", y="averagePrice", color="propertyType",
                    title="Cumulative Property Price Trend",
                    labels={"averagePrice": "Average Price ($)", "date": "Date"})
    st.plotly_chart(fig_area, use_container_width=True)

with r3c4:    
    # 🎯 **4️⃣ Box Plot - Price Distribution**
    fig_box = px.box(df_filtered_prop_data, x="propertyType", y="averagePrice",
                    title="Price Distribution by Property Type",
                    labels={"averagePrice": "Average Price ($)", "propertyType": "Property Type"})
    st.plotly_chart(fig_box, use_container_width=True)

#with r3c5:    
    # 🎯 **5️⃣ Scatter Plot - Price vs. Property Size (If Data Exists)**
#    if "LivingArea" in df_filtered_prop_data.columns:
#        fig_scatter = px.scatter(df_filtered, x="LivingArea", y="averagePrice", color="propertyType",
#                                title="Price vs Living Area",
#                                labels={"averagePrice": "Price ($)", "LivingArea": "Living Area (SqFt)"},
#                                size_max=10)
#        st.plotly_chart(fig_scatter, use_container_width=True)

print("---------------------------------------------------------------------------------------------------------------->>> end")