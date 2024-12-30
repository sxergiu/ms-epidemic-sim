import pandas as pd

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

def display_rates(region, infection_rate, recovery_rate):

    if infection_rate is not None:
        print(f"Infection rate for {region}: {infection_rate:.2%}")
    else:
        print(f"Infection rate for {region}: Data not available.")
    
    if recovery_rate is not None:
        print(f"Recovery rate for {region}: {recovery_rate:.2%}")
    else:
        print(f"Recovery rate for {region}: Data not available.")

def extract_probabilities( filepath='coronavirus_epidemic_dataset.csv', selected_region='France' ):

    region_data = load_and_filter_data(filepath, selected_region)

    if region_data is not None:
        infection_rate, recovery_rate = calculate_infection_and_recovery_rates(region_data)
        display_rates(selected_region, infection_rate, recovery_rate)

        return infection_rate , recovery_rate


if __name__ == "__main__":
    extract_probabilities()