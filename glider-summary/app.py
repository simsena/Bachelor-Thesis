import streamlit as st 
import xarray as xr
import cmocean
import matplotlib.pyplot as plt
import tempfile, os
import plotly.graph_objects as go
import matplotlib
import numpy as np

#https://docs.streamlit.io/develop/api-reference/configuration/st.set_page_config
st.set_page_config(page_title= "Glider Mission Summary", layout="wide", initial_sidebar_state="auto")

def cmap_to_plotly(cmap, n=256):
    xs = np.linspace(0, 1, n)
    return [[float(x), matplotlib.colors.to_hex(cmap(x))] for x in xs]


# Adds a map showing the track of the glider
def plot_track(ds):
    lat = ds["LATITUDE"].mean("PRES").values #.means to get a single value instead of multiple for each profile
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

    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xlabel("Longitude [°E]")
    ax.set_ylabel("Latitude [°N]")
    ax.set_title("Glider track")
    ax.tick_params(axis="x", rotation=45) #rotate x-axis labels for better readability

    return fig

# copilot prompt: "sidebar should show the metadata if it is available in the file"
def get_metadata_value(attrs, key, default="-"):
    value = attrs.get(key)
    if value is None or value == "" or str(value).lower() == "nan":
        return default
    return value

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
    # Filter variables and only keep those present in the dataset
    variables = [v for v in ["TEMP", "PSAL", "DOX2", "FLU2", "TURB"] if v in ds.data_vars]

    # https://docs.streamlit.io/develop/api-reference/layout/st.tabs
    tab_labels = ["Overview"] + variables
    tabs = st.tabs(tab_labels)
    with tabs[0]:

    # Plot the track of the glider if latitude and longitude are in the dataset
    # https://docs.streamlit.io/develop/api-reference/layout/st.columns
    # Add columns, left being the track and right being the profile plots
        left_col, right_col = st.columns([1, 2])
        with left_col:
            if "LATITUDE" in ds and "LONGITUDE" in ds:
                st.pyplot(plot_track(ds), use_container_width=False) # use_container_width = False makes the plot smaller than the full width of the page
            else:
                st.info("No coordinates in this file.")
            st.divider()

        with right_col:
            fig, axs = plt.subplots(len(variables),1,figsize=(8, 14), constrained_layout=True, sharex = True, squeeze=False) #https://matplotlib.org/stable/gallery/subplots_axes_and_figures/subplots_demo.html
    # Plot each measurement against pressure in a separate subplot
            for ax, v in zip(axs.flat, variables):
                ds[v].plot(y="PRES", ax=ax, cmap=CMAPS[v], yincrease=False, robust = True, center = False , cbar_kwargs={"label": LABELS[v]}) # yincrease = False makes the y-axis go from top to bottom 
                # center = False makes the colorbar not centered around 0. Since chlorphyll and turbidity are always positive. The slightly negative values seem to be just noise. 
                ax.spines['right'].set_visible(False)         

    # Hide x labels and add add lable to bottom plot
            for ax in axs.flat:
                ax.label_outer()
            axs.flat[-1].set_xlabel("Profile index")

    #Add metadata to the sidebar 
            with st.sidebar:
                st.header("Metadata")
                metadata_fields = [
                    ("Title of the file", "title"),
                    ("Institution", "institution"),
                    ("Sea name", "sea_name"),
                    ("Deployment ship name", "deployment_ship_name"),
                    ("Coverage time start", "time_coverage_start"),
                    ("Coverage time end", "time_coverage_end"),
                    ("Data mode", "data_mode"),
                ]

                for label, key in metadata_fields:
                    st.write(f"**{label}:**", get_metadata_value(ds.attrs, key))

    

            st.pyplot(fig) 

    for tab, v in zip(tabs[1:], variables):
        with tab:
            st.write(f"### {LABELS[v]}")
            vmin = float(np.nanmin(ds[v].values))
            vmax = float(np.nanmax(ds[v].values))
            col_min, col_max = st.columns(2)
            col_min.metric("Minimum", f"{vmin:.2f}")
            col_max.metric("Maximum", f"{vmax:.2f}")


            zmin = float(np.nanpercentile(ds[v].values, 2))
            zmax = float(np.nanpercentile(ds[v].values, 98))

            # https://plotly.com/python/heatmaps/
            fig = go.Figure(data = go.Heatmap(
                z=ds[v].values.T,
                x=ds["PROFILE_INDEX"].values, 
                y=ds["PRES"].values, 
                colorscale=cmap_to_plotly(CMAPS[v]),
                zmin=zmin,
                zmax=zmax, 
                colorbar=dict(title=LABELS[v])))
            
            fig.update_layout(
            xaxis_title="Profile index",
            yaxis_title="Pressure [dbar]",
            )
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig)
            



else:
    st.info("Please upload a .nc-file.")







