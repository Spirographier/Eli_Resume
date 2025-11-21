import pandas as pd
import numpy as np
import re
import glob
import os

def print_pretty_dict(dictionary):
    max_key_length = max(len(key) for key in dictionary.keys())
    for key, value in dictionary.items():
        print(f"{key:<{max_key_length}} : {value}")

def read_data(vstate, vchamber):
    # Specifies the base directory
    directory_path = '/Users/elistettner/Documents/Fairvote Internship 23-24'

    # Uses glob.glob() to match files with a wildcard pattern
    file_pattern = f"{directory_path}/state{vchamber}/{vchamber}_{vstate}*.csv"
    matching_files = glob.glob(file_pattern)

    if matching_files:
        df_full = pd.read_csv(matching_files[0], index_col=False)
            # matching_files[0] takes the first glob match
            # which should be the only the one

        #extracts average row
        average_row = df_full.iloc[-1]
        average_row = average_row.copy()
        average_row['AAPI'] = average_row['Asian'] + average_row['Pacific']

        #defines df as df_full sans first and last row
        df = df_full.iloc[1:-1]
        df = df.copy()
        df['AAPI'] = df['Asian'] + df['Pacific']
        columns_to_drop = ['Asian', 'Pacific']
        df.drop(columns=columns_to_drop, inplace=True)


        # Extract the number within parentheses and assign it to 'numseats'
        disallowed_states = ["ID", "ND", "NJ", "WA"]
        if vstate in allowed_states and vchamber == "lower":
            i = 2
        else:
            i = 1
        #This regex works with two digit amounts of reps
        df['numseats'] = df['ID'].str.extract(r'\((\d+)\)').fillna(i).astype(int) #extracts string from ID column as interger
        total_members = df['numseats'].sum()


        # Calculate the two-party vote share
        democratic_abs = df['Dem'] # these are strings
        republican_abs = df['Rep']
        share = (democratic_abs + republican_abs) #combination string
        df = df.loc[:, df.columns] #create copy of all columns
        df['Two Party Vote Share'] = share #assigns string to a column in the data frame
        safe_democratic_seats = 0
        safe_republican_seats = 0

        # Creates boolean test for Democratic wins 
        dem_2share = democratic_abs / share #calculates two party vote share for democrats
        safe_dem = dem_2share > 0.53 # 53% safe seat test

        #Calculate actual number of Democratic seats
        dem_seatwins = df['numseats'] * safe_dem.astype(int) 
            #takes number of seats per district * the boolean win series interpreted as an intergral
        safe_democratic_seats = sum(dem_seatwins)
        percentage_dem = safe_democratic_seats / total_members


        # Creates boolean test for Republican wins 
        rep_2share = republican_abs / share  #calculates two party vote share for GOP
        safe_rep = rep_2share > 0.53 # 53% safe seat test

        #Calculate actual number of Republican seats
        rep_seatwins = df['numseats'] * safe_rep.astype(int)
        safe_republican_seats = sum(rep_seatwins)
        percentage_rep = safe_republican_seats / total_members

        swing_seats = total_members - (safe_democratic_seats + safe_republican_seats)



        # Create columns for each racial group
        seat_count_by_group = {}
        racial_group_majority = {} 
        racial_groups = ['AAPI', 'Black', 'Hispanic', 'White', 'Native']
        for group in racial_groups:
            df[f'{group} Majority'] = df[group].between(0.5, 1)
            df[f'{group} Seats'] = df[group].between(0.5, 1) * df['numseats']
            seat_count_by_group[group] = df[f'{group} Seats']
            racial_group_majority[group] = df[f'{group} Majority']

        # Coalition seat condition
        df['Coalition Win'] = sum(racial_group_majority.values()) == 0 # boolean test of the dictionary
        df['Coalition Seats'] = df['Coalition Win'] * df['numseats'] #account for multimember
        total_coalition_seats = df['Coalition Seats'].sum() #sums it
        total_coalition_percentage = total_coalition_seats / total_members #percentages


        parties = ['Dem', 'Rep']
        party_vap_dict = {}  # Create a dictionary to store the variables

        for party in parties:
            party_vap_dict[f'{party}_VAP'] = round(average_row[party],4)

        data_dict = {}

        for group, seat_count_df in seat_count_by_group.items():
            total_seats = seat_count_df.sum()
            percentage = (total_seats / total_members).round(2)
            xVAP = round(average_row[f'{group}'], 4)

            data_dict[f"{group} Total Seats"] = total_seats
            data_dict[f"{group} Seat Percentage"] = percentage
            data_dict[f"{group} Vote-share Percentage"] = xVAP

        
        data_dict["ZID"] = f"{vstate}_{vchamber}"
        data_dict["State"] = vstate
        data_dict["Chamber"] = vchamber
        data_dict["Total Coalition Seats"] = total_coalition_seats
        data_dict["Coalition Seats Percentage"] = total_coalition_percentage
        data_dict["Total Members in Chamber"] = total_members
        data_dict["Total Safe Seats for Democrats"] = safe_democratic_seats
        data_dict["Seat Percentage for Democrats"] = percentage_dem
        data_dict["Dem VAP Percentage"] = party_vap_dict['Dem_VAP']
        data_dict["Total Safe Seats for Republicans"] = safe_republican_seats
        data_dict["Seat Percentage for Republicans"] = percentage_rep
        data_dict["Rep VAP Percentage"] = party_vap_dict['Rep_VAP']
        data_dict["Total Toss-Up Seats"] = swing_seats
        return data_dict
    else:
        print(f"No matching CSV files found for pattern: {file_pattern}")
    
# List of state postal codes and chambers
state_codes = [
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
]

chambers = ["upper", "lower"]  

list_of_dfs = []

for vchamber in chambers:
    for vstate in state_codes:
        state_data_dict = read_data(vstate, vchamber)
            #assigns the returning dictionary to state_data_entry
        if state_data_dict is not None:
            # takes the new state data dictionary
            new_df = pd.DataFrame([state_data_dict])
            list_of_dfs.append(new_df)
            
        else:
            print(f"ERROR for {vchamber} {vstate}")

final_df = pd.concat(list_of_dfs, ignore_index=True)
final_df = final_df.set_index('ZID')
# Save the combined DataFrame to a CSV file
final_df.to_csv("processed_state_data.csv")

print(final_df)