import streamlit as st
import pandas as pd
import numpy as np
import plotly.express  as ff

###################################
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import JsCode

###################################

from functionforDownloadButtons import download_button

###################################

def is_float (element: any) -> bool:
    try:
        float(element)
        return True
    except ValueError:
        return False


def MSA_parameter (df, lim):

    listdf = []
    for dfcol, limcol in zip(df, lim):
        if not is_float(lim[limcol][1]) or not np.issubdtype(df[dfcol].dtype, np.number):
            print("skipped " + dfcol + " where the unit is " + str(lim[limcol][2]) + " and lower spec is : "
                  + str(lim[limcol][0]) + " and higher is :" + str(lim[limcol][1]))
            continue
        returndf = dict()
        returndf['name'] = dfcol
        returndf['max'] = float(lim[limcol][1])
        returndf['min'] = float(lim[limcol][0])
        returndf['mean'] = df[dfcol].mean()
        returndf['std'] = df[dfcol].std()
        #returndf['std'] = 9999999999999999999999 # safety deviding by 0 error
        returndf['cpkl'] = (returndf['mean'] - returndf['min'])/(3*returndf['std'])
        returndf['cpkh'] = (returndf['max'] - returndf['mean'])/(3*returndf['std'])
        returndf['cpk'] = min(returndf['cpkl'], returndf['cpkh'])
        returndf['cp'] = (returndf['max']-returndf['min'])/6*returndf['std']
        if returndf['cpk'] < 1.63:
            returndf['issue'] = True
        else:
            returndf['issue'] = False
        listdf.append(returndf)
    return listdf



def _max_width_():
    max_width_str = f"max-width: 1800px;"
    st.markdown(
        f"""
    <style>
    .reportview-container .main .block-container{{
        {max_width_str}
    }}
    </style>    
    """,
        unsafe_allow_html=True,
    )

st.set_page_config(page_icon="✂️", page_title="Logdata Histogram Viewer by SCL")


st.image(
    "https://media.melexis.com/Assets/img/melexis_logo-baseline.svg",
    width=100,
)

st.title("Logdata Histogram Viewer by SCL")

# st.caption(
#     "PRD : TBC | Streamlit Ag-Grid from Pablo Fonseca: https://pypi.org/project/streamlit-aggrid/"
# )


# ModelType = st.radio(
#     "Choose your model",
#     ["Flair", "DistilBERT (Default)"],
#     help="At present, you can choose between 2 models (Flair or DistilBERT) to embed your text. More to come!",
# )

# with st.expander("ToDo's", expanded=False):
#     st.markdown(
#         """
# -   Add pandas.json_normalize() - https://streamlit.slack.com/archives/D02CQ5Z5GHG/p1633102204005500
# -   **Remove 200 MB limit and test with larger CSVs**. Currently, the content is embedded in base64 format, so we may end up with a large HTML file for the browser to render
# -   **Add an encoding selector** (to cater for a wider array of encoding types)
# -   **Expand accepted file types** (currently only .csv can be imported. Could expand to .xlsx, .txt & more)
# -   Add the ability to convert to pivot → filter → export wrangled output (Pablo is due to change AgGrid to allow export of pivoted/grouped data)
# 	    """
#     )
#
#     st.text("")


c29, c30, c31 = st.columns([1, 6, 1])

with c30:

    uploaded_file = st.file_uploader(
        "",
        key="1",
        help="To activate 'wide mode', go to the hamburger menu > Settings > turn on 'wide mode'",
    )

    if uploaded_file is not None:
        file_container = st.expander("Check your uploaded .csv")
        data = pd.read_csv(uploaded_file, low_memory=False, skiprows=[1,2,3])
        uploaded_file.seek(0)
        limits = pd.read_csv(uploaded_file, nrows=4)
        uploaded_file.seek(0)
        file_container.write(data)

    else:
        st.info(
            f"""
                👆 Upload a .csv file first. Download it from here: [data-convertor](https://esb.sensors.elex.be/data-converter/)
                """
        )

        st.stop()

from st_aggrid import GridUpdateMode, DataReturnMode

gb = GridOptionsBuilder.from_dataframe(data)
# enables pivoting on all columns, however i'd need to change ag grid to allow export of pivoted/grouped data, however it select/filters groups
gb.configure_default_column(enablePivot=True, enableValue=True, enableRowGroup=True)
gb.configure_selection(selection_mode="multiple", use_checkbox=True)
gb.configure_side_bar()  # side_bar is clearly a typo :) should by sidebar
gridOptions = gb.build()

st.success(
    f"""
        💡 Tip! Hold the shift key when selecting rows to select multiple rows at once!
        """
)
listMSA = MSA_parameter(data[data.columns[100:]], limits[limits.columns[100:]])
paramwithissue = []
for param in listMSA:
    if param['issue']:
        paramwithissue.append(param['name'])

options = st.multiselect("Select the Parameter name for the histogram", paramwithissue)
Parameters = ['site number','D_ChipId_ID','BIN','msa_step'] + options
df = data[Parameters]


#df = pd.DataFrame(response["selected_rows"])

st.subheader("Selected Parameter histogram will appear below 👇 ")
st.text("")

#st.table(df)

st.text("")


for col in options:
    labels = [f"CS{cs}" for cs in range(1, data['site number'].max() + 1)]
    fig = ff.histogram(data, x=col, color='BIN', pattern_shape="site number")
    fig.add_vline(x=float(limits[col][1]), line=dict(
        color="LightSeaGreen",
        width=4,
        dash="dashdot",
    ))
    fig.add_vline(x=float(limits[col][0]), line=dict(
        color="LightSeaGreen",
        width=4,
        dash="dashdot",
    ))
    fig.update_layout(
        paper_bgcolor="lightgrey"
    )
    st.plotly_chart(fig)



c29, c30, c31 = st.columns([1, 1, 2])

with c29:

    CSVButton = download_button(
        df,
        "File.csv",
        "Download to CSV",
    )

with c30:
    CSVButton = download_button(
        df,
        "File.csv",
        "Download to TXT",
    )