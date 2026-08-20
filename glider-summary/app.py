import streamlit as st 
import xarray as xr
import cmocean
import matplotlib.pyplot as plt
import tempfile, os


st.title("Glider Mission Summary")

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

    ds = xr.open_dataset(temp_path).load() 
    os.remove(temp_path)  


#color makes a big difference. you can see it for the FLU2 variable the best 
    CMAPS = {
    "TEMP": cmocean.cm.thermal, "PSAL": cmocean.cm.haline,
    "DOX2": cmocean.cm.oxy, "FLU2": cmocean.cm.algae, "TURB": cmocean.cm.turbid,
}

    variables = ["TEMP", "PSAL", "DOX2", "FLU2", "TURB"]
    fig, axs = plt.subplots(len(variables),1,figsize=(8, 14), constrained_layout=True, sharex = True) #https://matplotlib.org/stable/gallery/subplots_axes_and_figures/subplots_demo.html

    for ax, v in zip(axs, variables):
        ds[v].plot(y="PRES", ax=ax, cmap=CMAPS[v], yincrease=False) #yincreas = false to flip surface to the top

# Hide x labels and tick labels for top plots and y ticks for right plots.
    for ax in axs.flat:
        ax.label_outer()

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







