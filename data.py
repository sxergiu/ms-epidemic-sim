import pandas as pd
import kagglehub

def load_and_filter_data(filepath, region):
    try:
        data = pd.read_csv(filepath)
        region_data = data[data['Country/Region'] == region]
        return region_data
    except FileNotFoundError:
        print("File not found. Please provide the correct file path.")
        return None

def calculate_infection_and_recovery_rates(region_data):
    confirmed = region_data[region_data['Case Type'] == 'Confirmed']
    recovered = region_data[region_data['Case Type'] == 'Recovered']
    deaths = region_data[region_data['Case Type'] == 'Deaths']
    
    total_confirmed_cases = confirmed['Count'].sum()
    total_recovered_cases = recovered['Count'].sum()
    total_deaths = deaths['Count'].sum()
    
    total_cases = total_confirmed_cases + total_recovered_cases + total_deaths
    
    infection_rate = total_confirmed_cases / total_cases 
    recovery_rate = total_recovered_cases / total_confirmed_cases 
    
    return infection_rate, recovery_rate

def calculate_vaccination_rate(vaccination_data, region_population, region_name):
    try:
        
        vaccinated = vaccination_data['people_vaccinated'].max()
        
        if region_population.empty:
            print(f"Population data for {region_name} not found.")
            return None
        
        average_population = (region_population['2020 Population'].iloc[0] + region_population['2022 Population'].iloc[0]) / 2
        
        vaccination_rate = vaccinated / average_population
        return vaccination_rate
    except KeyError:
        print("Required columns missing in vaccination or population data.")
        return None

def display_rates(region, infection_rate, recovery_rate, vaccination_rate):
    if infection_rate is not None:
        print(f"Infection rate for {region}: {infection_rate:.2%}")
    else:
        print(f"Infection rate for {region}: Data not available.")
    
    if recovery_rate is not None:
        print(f"Recovery rate for {region}: {recovery_rate:.2%}")
    else:
        print(f"Recovery rate for {region}: Data not available.")
    
    if vaccination_rate is not None:
        print(f"Vaccination rate for {region}: {vaccination_rate:.2%}")
    else:
        print(f"Vaccination rate for {region}: Data not available.")

def extract_probabilities(covid_filepath='coronavirus_epidemic_dataset.csv', 
                          vaccination_filepath='vaccination_dataset.csv', 
                          population_filepath = 'world_population_dataset.csv',
                          selected_region='France'):

    region_data = load_and_filter_data(covid_filepath, selected_region)

    vaccination_data = pd.read_csv(vaccination_filepath)
    vax_region_data = vaccination_data[vaccination_data['location'] == selected_region ]
    
    population_data = pd.read_csv(population_filepath)
    population_region_data = population_data[population_data['Country/Territory'] == selected_region ]

    if region_data is not None and vaccination_data is not None and population_data is not None:
        infection_rate, recovery_rate = calculate_infection_and_recovery_rates(region_data)
        vaccination_rate = calculate_vaccination_rate(vax_region_data, population_region_data, selected_region)
        display_rates(selected_region, infection_rate, recovery_rate, vaccination_rate)

        return infection_rate, recovery_rate, vaccination_rate

if __name__ == "__main__":
    extract_probabilities()
