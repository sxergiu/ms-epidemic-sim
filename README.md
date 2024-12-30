# Disease Spread Model Simulation 

![Simulation](./assets/blackplague.png)

## Overview
- **A SIR agent-based epidemic model simulation**, built using `pygame`. The simulation can be run with default parameters or with real-world data for specific countries.
The simulation provides a visual representation of SIR epidemic dynamics with parameters adjustable in real-time and other **user controls**. Beside the pygame window,
graphs are plotted concerning the impact of virus spread, vaccination use and also epidemic casulaties.

---

## Contents
- **Scripts**
  - Main simulation script
  - Data extraction script

- **Datasets**
  - Infection and recovery values from: https://www.kaggle.com/datasets/prashant111/coronavirus-daily-counts-data?resource=download&select=Coronavirus+daily+counts.csv
  - Vaccination values from: https://github.com/owid/covid-19-data
  - Reference country population from: https://www.kaggle.com/datasets/iamsouravbanerjee/world-population-dataset/data?select=world_population.csv

---

## Requirements
- Python 3.8+
- `pygame`
- `matplotlib`
- `pandas`
  
---

## Usage

### Running the simulation
 Run epidemic_sim.py
 For switching dataset usage, change **withDataset** in main script

### User Controls
 Z - add susceptible agent
 Q - infect random agent
 R - restart simulation
 0-6 - adjust parameters
 
### Simulation Graphs
1. **Output #1 Basic simulation**

   ![Infection Curve](./assets/graph.png)

2. **Ouput #2 Adding multiple agents**

   ![Recovery Curve](./assets/graph2.png)

3. **Output #3 Documented - France**

   ![Vaccination Curve](./assets/french_graph.png)

4. **Output #4 Documented - Taiwan**

   ![Combined Trends](./images/taiwan_graph.png)

---

## Acknowledgments

- This project is based on the SIR epidemic model and COVID-19 data sources.
- Visualization inspired by real-world epidemic dynamics.

---

