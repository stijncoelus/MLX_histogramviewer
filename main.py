import streamlit as st
import pandas as pd
import numpy as np
import plotly.figure_factory  as ff

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

    listdf = pd.DataFrame()
    for dfcol, limcol in zip(df, lim):
        if not is_float(lim[limcol][1]) or not np.issubdtype(df[dfcol].dtype, np.number):
            #print("skipped " + dfcol + " where the unit is " + str(lim[limcol][2]) + " and lower spec is : "
            #     + str(lim[limcol][0]) + " and higher is :" + str(lim[limcol][1]))
            continue
        maximum = float(lim[limcol][1])
        minimum = float(lim[limcol][0])
        mean = df[dfcol].mean()
        std = df[dfcol].std()
        if std <= 0 or pd.isna(std):
            continue
        cpkl = (mean - minimum)/(3*std)
        cpkh = (maximum - mean)/(3*std)
        cpk = min(cpkl, cpkh)
        cp = (maximum-minimum)/6*std
        issue = False
        if cpk < 1.63:
            issue = True
        row = pd.DataFrame(data={'name': [dfcol, ],
                    'max':  [maximum, ],
                    'min':  [minimum, ],
                    'mean': [mean, ],
                    'std': [std, ],
                    'cpkl': [cpkl, ],
                    'cpkh': [cpkh, ],
                    'cpk': [cpk, ],
                    'cp': [cp, ],
                    'issue': [issue, ]
                    })

        listdf = pd.concat([listdf, row], ignore_index=True)
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
RemoveFails = st.checkbox('Only BIN1')

if RemoveFails:
    data = data[data['BIN'] < 200]
listMSA = MSA_parameter(data[data.columns[100:]], limits[limits.columns[100:]])
st.dataframe(listMSA)
paramwithissue = listMSA[listMSA['issue']]['name']

options = st.multiselect("Select the Parameter name for the histogram", paramwithissue)
Parameters = ['site number','D_ChipId_ID','BIN','msa_step'] + options
df = data[Parameters]


#df = pd.DataFrame(response["selected_rows"])

st.subheader("Selected Parameter histogram will appear below 👇 ")
st.text("")


#st.table(df)

st.text("")



for col in options:
    #labels = [f"CS{cs}" for cs in range(1, data['site number'].max() + 1)]
    fig = ff.create_distplot([data[col].dropna()], group_labels=[col], bin_size=[(float(limits[col][1])-float(limits[col][0]))/100])
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
        paper_bgcolor="lightgrey",
        plot_bgcolor ="white"
    )
    st.plotly_chart(fig)



c29, c30, c31 = st.columns([1, 1, 2])

with c29:

    CSVButton = download_button(
        df,
        "File.csv",
        "Download Selected",
    )

with c30:
    CSVButton = download_button(
        listMSA,
        "File.csv",
        "Download MSA",
    )
