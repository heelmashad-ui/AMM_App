import io
import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="AMMP Benefits Calculator",
    page_icon="🐄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Reference Data
REF = {
    'temps': {
        'Alameda': {
            'station': 'HAYWARD',
            'F': [
                50,
                52.5,
                55.2,
                56.7,
                60.6,
                63.7,
                66.1,
                66.5,
                66.2,
                62.2,
                55.8,
                50.5,
            ],
        },
        'Fresno': {
            'station': 'FRESNO',
            'F': [
                47.3,
                51.3,
                57.1,
                61.2,
                70.5,
                77.3,
                83.4,
                81.6,
                76.1,
                65.6,
                54.9,
                47.1,
            ],
        },
        'Merced': {
            'station': 'MERCED',
            'F': [
                44.9,
                49.4,
                54.2,
                58.5,
                67.7,
                74.3,
                78.8,
                77,
                72.3,
                63.3,
                52.8,
                45.6,
            ],
        },
        'Stanislaus': {
            'station': 'MODESTO',
            'F': [
                46.5,
                51.2,
                56.4,
                60.2,
                68.3,
                74.9,
                79.2,
                77.8,
                73.4,
                64.3,
                54.1,
                47.1,
            ],
        },
        'Tulare': {
            'station': 'VISALIA',
            'F': [
                46.6,
                51.7,
                56.7,
                61.3,
                68.7,
                75.3,
                80.4,
                78.9,
                74,
                65.3,
                53.8,
                46.1,
            ],
        },
    },
    'livestock': [
        {
            'name': 'Lactating Dairy Cows (freestall)',
            'mass': 680,
            'Bo': 0.24,
            'VS': 7.7588,
        },
        {
            'name': 'Lactating Dairy Cows (open lot)',
            'mass': 680,
            'Bo': 0.24,
            'VS': 7.7588,
        },
        {'name': 'Cattle: dry cows', 'mass': 684, 'Bo': 0.24, 'VS': 3.8030},
        {
            'name': 'Cattle: heifers (on feed)',
            'mass': 407,
            'Bo': 0.17,
            'VS': 3.4351,
        },
        {'name': 'Cattle: bulls', 'mass': 874, 'Bo': 0.17, 'VS': 5.2790},
    ],
    'practices2018': [
        '1a - Pasture based management - conversion to pasture management or'
        ' increased time at pasture',
        '2a - Installation of compost bedded pack barn',
        '3a - Solid separation with open solar drying',
        '3f - Solid separation with composting (in vessel or aerated static'
        ' pile)',
        '4a - Scrape conversion with open solar drying',
    ],
    'solidsep': [
        'none',
        'weeping wall',
        'stationary screen',
        'vibrating screen',
        'screw press',
        'centrifuge',
    ],
    'sep_eff': {
        'none': 0.0,
        'weeping wall': 0.65,
        'stationary screen': 0.30,
        'vibrating screen': 0.15,
        'screw press': 0.25,
        'centrifuge': 0.50,
    },
    'fuel_ef': {
        'Diesel (gal)': 13.50751,
        'Gasoline (gal)': 11.51814,
        'Electricity (kWh)': 0.2106,
    },
}


def calculate_emissions(inputs):
  ls_info = next(
      (
          item
          for item in REF['livestock']
          if item['name'] == inputs['livestock_type']
      ),
      REF['livestock'][0],
  )
  num_head = inputs['head_count']
  total_vs_annual = num_head * ls_info['VS'] * 365
  baseline_mcf = 0.70

  sep_eff = REF['sep_eff'].get(inputs['solid_separator'], 0.0)
  if inputs['flocculant'] != 'No':
    sep_eff = min(0.80, sep_eff * 1.3)

  ch4_baseline_kg = total_vs_annual * ls_info['Bo'] * 0.67 * baseline_mcf
  ch4_baseline_mt = ch4_baseline_kg / 1000.0

  vs_liquid = total_vs_annual * (1.0 - sep_eff)
  vs_solid = total_vs_annual * sep_eff

  ch4_project_liquid = (
      vs_liquid
      * ls_info['Bo']
      * 0.67
      * baseline_mcf
      * (1.0 - inputs['flush_reduction_pct'])
  )
  ch4_project_solid = vs_solid * ls_info['Bo'] * 0.67 * 0.010
  ch4_project_mt = (ch4_project_liquid + ch4_project_solid) / 1000.0

  co2e_baseline = ch4_baseline_mt * 25.0
  co2e_project = ch4_project_mt * 25.0
  co2e_reduction_annual = max(0.0, co2e_baseline - co2e_project)

  return {
      'co2e_baseline': co2e_baseline,
      'co2e_project': co2e_project,
      'co2e_reduction_annual': co2e_reduction_annual,
      'co2e_reduction_10yr': co2e_reduction_annual * 10.0,
  }


st.title('🐄 AMMP Benefits Calculator')

county = st.selectbox('Select County:', options=list(REF['temps'].keys()))
livestock_type = st.selectbox(
    'Livestock Category:', options=[x['name'] for x in REF['livestock']]
)
head_count = st.number_input('Head Count:', min_value=1, value=1000, step=50)
proposed_practice = st.selectbox(
    'Proposed Practice:', options=REF['practices2018']
)
solid_separator = st.selectbox(
    'Solid Separator:', options=REF['solidsep']
)
flocculant = st.selectbox('Flocculant Added:', options=['No', 'Yes'])
flush_reduction = st.slider(
    'Flush Reduction %:', min_value=0, max_value=100, value=30
)

results = calculate_emissions({
    'county': county,
    'livestock_type': livestock_type,
    'head_count': head_count,
    'proposed_practice': proposed_practice,
    'solid_separator': solid_separator,
    'flocculant': flocculant,
    'flush_reduction_pct': flush_reduction / 100.0,
})

m1, m2, m3 = st.columns(3)
m1.metric('Baseline GHG', f"{results['co2e_baseline']:,.1f} tCO2e/yr")
m2.metric('Project GHG', f"{results['co2e_project']:,.1f} tCO2e/yr")
m3.metric('10-Year GHG Benefit', f"{results['co2e_reduction_10yr']:,.1f} tCO2e")
