import streamlit as st 
import xarray as xr
import cmocean
import matplotlib.pyplot as plt
import tempfile, os


# Adds a track map
def plot_track(ds):
    lat = ds["LATITUDE"].mean("PRES").values
    lon = ds["LONGITUDE"].mean("PRES").values
    order = ds["PROFILE_INDEX"].values

    fig, ax = plt.subplots(figsize=(5, 4.3), constrained_layout=True)
    #Co-Pilot prompt:"how can i add a color legend to my trackplot?"
    sc = ax.scatter(
        lon, lat,
        c=order,
        cmap="viridis",
        s=14,
        zorder=2
    )

    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label("Profile index")

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Glider track")

    return fig


#https://docs.streamlit.io/develop/api-reference/configuration/st.set_page_config
st.set_page_config(page_title= "Glider Mission Summary", layout="wide", initial_sidebar_state="auto")


#https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader

uploaded_file = st.file_uploader(
    "Drop a NetCDF file here!",
    type=["nc"],
    accept_multiple_files = False)

if uploaded_file is not None:
#https://docs.kanaries.net/topics/Streamlit/streamlit-upload-file

    with tempfile.NamedTemporaryFile(delete=False, suffix=".nc") as temp:
        temp.write(uploaded_file.getvalue())
        temp_path = temp.name

    ds = xr.open_dataset(temp_path)
    ds.load()      
    ds.close()     
    os.remove(temp_path) 


#color makes a big difference. you can see it for the FLU2 variable the best 
# Set cmocean colormaps for the corresponding values
    CMAPS = {
    "TEMP": cmocean.cm.thermal, "PSAL": cmocean.cm.haline,
    "DOX2": cmocean.cm.oxy, "FLU2": cmocean.cm.algae, "TURB": cmocean.cm.turbid,
    }

#Set standardized lables
    LABELS = {
        "TEMP": "Temperature [°C]", "PSAL": "Salinity [PSU]", "DOX2": "Oxygen [µmol kg⁻¹]",
        "FLU2": "Chlorophyll [mg m⁻³]", "TURB": "Turbidity [NTU]",
    }

    variables = ["TEMP", "PSAL", "DOX2", "FLU2", "TURB"]
    variables = [v for v in ["TEMP", "PSAL", "DOX2", "FLU2", "TURB"] if v in ds.data_vars]

    if "LATITUDE" in ds and "LONGITUDE" in ds:
        st.pyplot(plot_track(ds), use_container_width=False)
    else:
        st.info("No coordinates in this file.")
    st.divider()


    fig, axs = plt.subplots(len(variables),1,figsize=(8, 14), constrained_layout=True, sharex = True) #https://matplotlib.org/stable/gallery/subplots_axes_and_figures/subplots_demo.html

    for ax, v in zip(axs, variables):
        ds[v].plot(y="PRES", ax=ax, cmap=CMAPS[v], yincrease=False, robust = True, cbar_kwargs={"label": LABELS[v]}) #yincreas = false to flip surface to the top
        ax.set_title("")
        ax.set_ylabel("Pressure [dbar]")

# Hide x labels and tick labels for top plots and y ticks for right plots.
    for ax in axs.flat:
        ax.label_outer()
    axs[-1].set_xlabel("Profile index")

    with st.sidebar:
        st.header("Metadata")
        # to do see what i want to include here 
        st.write("**Title of the file:**", ds.attrs['title'])
        st.write("**Institution:**", ds.attrs['institution'])
        st.write("**Sea name:**", ds.attrs['sea_name'])
        st.write("**Deployment ship name:**", ds.attrs['deployment_ship_name'])
        st.write("**Coverage time start:**", ds.attrs['time_coverage_start'])
        st.write("**Coverage time end:**", ds.attrs['time_coverage_end'])
        st.write("**Data mode:**", ds.attrs['data_mode'])

    

    st.pyplot(fig) 

else:
    st.info("Please upload a .nc-file.")







