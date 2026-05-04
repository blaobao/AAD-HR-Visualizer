from astroquery.gaia import Gaia
from astroquery.vizier import Vizier
import pandas as pd
import astropy.coordinates as coord
import astropy.units as u
import math
import streamlit as st

Gaia.ROW_LIMIT = -1
pd.options.plotting.backend = "plotly"
st.set_page_config(layout="wide")
st.title("cool color mag")

#cool coordinate maker. The frame represents how the coordinate system will be in RA / DEC
coords = {
    "Messier 13": {"coordinate": coord.SkyCoord(ra=250.421*u.deg, dec=36.460*u.deg, frame='icrs'), "parsecs": 7100, "parallax": 0.14, "radius": 0.1},
    "Barnard's Loop": {"coordinate": coord.SkyCoord(ra=81.875*u.deg, dec=-3.966*u.deg, frame='icrs'), "parsecs": 440, "parallax": 2.27, "radius": 0.5}
    }

options = list(coords.keys()) + ["Custom..."]
selected = st.sidebar.selectbox("Choose a Cluster", options)
if selected == "Custom...":
    st.sidebar.markdown("### Custom Coordinates")
    
    custom_ra = st.sidebar.number_input("Right Ascension (degrees)", min_value=0.0, max_value=360.0, value=180.0)
    custom_dec = st.sidebar.number_input("Declination (degrees)", min_value=-90.0, max_value=90.0, value=0.0)
    parsecs = st.sidebar.number_input("Distance (parsecs)", min_value=1.0, value=1000.0)
    parallax = st.sidebar.number_input("Parallax (mas)", value=1.00)
    search_radius = st.sidebar.number_input("Search Radius (degrees)", min_value=0.01, max_value=1.0, value=0.1)
    
    # back into astropy!!
    coordinate = coord.SkyCoord(ra=custom_ra*u.deg, dec=custom_dec*u.deg, frame='icrs')
    coords["Custom..."] = {"coordinate": coordinate, "parsecs": parsecs, "parallax": parallax, "radius": search_radius}

parsecs = coords[selected]["parsecs"]
coordinate = coords[selected]["coordinate"]
parallax = coords[selected]["parallax"]
rad = coords[selected]["radius"]

tolerance = 0.2
upperBound = parallax + tolerance
lowerBound = parallax - tolerance

if st.sidebar.button("Generate Graph"):

    with st.spinner("Downloading data from VizieR..."):
        queryViz = Vizier(columns=['Source', 'Gmag', 'BP-RP', 'pmRA', 'pmDE', 'Plx', 'e_Plx'], row_limit=-1)
        #Query setup. Source = id thing. Gmag = Apparent magnitude. BP-RP = color index of star. pmRA/pmDE = Right Asc/Declination

        results = queryViz.query_region(coordinate, radius = rad*u.deg, catalog='I/355/gaiadr3')
        #Query thingy within this radius from gaia

        #Pandas conversion and math
        data = results[0].to_pandas()
        data = data.dropna(subset=['Gmag', 'BP-RP', 'pmRA', 'pmDE', 'Plx', 'e_Plx'])
        data = data[(data['Plx'] >= lowerBound) & (data['Plx'] <= upperBound) & (data['e_Plx'] < 0.2)].copy()
        data['AbsMag'] = data['Gmag'] +5 - 5 * math.log10(parsecs)

        #setting up the color-magnitude graph (same as HR diagram but with different axes)
        cm = data[['BP-RP', 'AbsMag']]
        cm.columns = ['Color', 'Absolute Magnitude']
        fig = cm.plot.scatter(x = 'Color', y = 'Absolute Magnitude', opacity=0.4, color='Color', color_continuous_scale='RdBu_r')
        fig.update_yaxes(autorange="reversed")
        fig.update_layout( plot_bgcolor='rgba(20,20,20,255)', paper_bgcolor='rgba(0,0,0,255)', font_color="white")
        fig.update_xaxes(gridcolor='rgba(35,35,35,255)')
        fig.update_yaxes(gridcolor='rgba(35,35,35,255)')
        fig.update_xaxes(zeroline=False)
        fig.update_yaxes(zeroline=False)

        #show the graph
        st.plotly_chart(fig, use_container_width=True)

#Runcmd: python -m streamlit run app.py