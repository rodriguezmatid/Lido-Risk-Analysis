import logging, math, pandas as pd, functions, requests, numpy as np
pd.options.display.float_format = '{:,.2f}'.format

SLOTS_PER_EPOCH = 32
SECONDS_PER_SLOT = 12
BASE_REWARDS_PER_EPOCH = 4
MAX_EFFECTIVE_BALANCE = 2**5 * 10**9
EFFECTIVE_BALANCE_INCREMENT = 2**0 * 10**9
PROPOSER_WEIGHT=8
SYNC_COMMITTEE_SIZE=2**9 # (= 512)	Validators	
EPOCHS_PER_SYNC_COMMITTEE_PERIOD=2**8 # (= 256)	epochs	~27 hours
MAX_VALIDATOR_COUNT = 2**19 # (= 524,288)

states = ['scenario_1', 'scenario_2', 'scenario_3']

def create_and_display_results(loss_slashings, loss_offline, lidostakeddeposits, lido_insurance_fund):
    """
    Creates and displays a DataFrame with loss results for Lido's scenarios.

    Parameters:
    loss_slashings (list): List of total loss due to slashings for each scenario.
    loss_offline (list): List of total loss due to validators being offline for each scenario.
    lidostakeddeposits (list): List of Lido's staked deposits for each scenario.
    lido_insurance_fund (list): List of Lido's insurance fund amounts for each scenario.

    Returns:
    DataFrame: A pandas DataFrame containing the calculated results.
    """
    df_result = pd.DataFrame({'loss_slashings': loss_slashings, 'loss_offline': loss_offline}, index=['scenario_1', 'scenario_2', 'scenario_3'])
    df_result['total_loss'] = df_result.loss_slashings + df_result.loss_offline
    df_result['lidostakeddeposits'] = lidostakeddeposits
    df_result['lido_insurance_fund'] = lido_insurance_fund
    df_result['%_of_lido_deposits'] = df_result.total_loss / df_result.lidostakeddeposits * 100
    df_result['%_of_lido_funds'] = df_result.total_loss / df_result.lido_insurance_fund * 100

    pd.options.display.float_format = '{:,.2f}'.format
    print(df_result[['total_loss', 'loss_slashings', 'loss_offline', '%_of_lido_deposits', '%_of_lido_funds']])
    return df_result

def get_scenario(scenario):

    """
    Processes a given scenario to calculate the total loss due to slashings and offline penalties for Lido validators.

    This function calculates the total loss incurred by Lido validators in a given scenario, considering both
    slashing penalties and offline penalties. It calculates these losses for each item in the 'scenario' list, 
    which represents different states of the Lido validators.

    Parameters:
    scenario (list of lists): A list where each element is a list representing a scenario. Each scenario is expected 
                              to contain information about the number of validators offline, the duration they are offline,
                              and the number of validators slashed.

    Returns:
    None: The function prints a DataFrame containing the calculated losses and their impact on Lido's deposits and funds.

    The function performs the following steps:
    - Calculate losses due to slashing and store them in `result_list_sl`.
    - Calculate losses due to validators being offline and store them in `result_list`.
    - Create a DataFrame `df_result` to combine and display the results.
    - Print the DataFrame with relevant loss information and percentages.
    """

    result_list_sl = [] # Initialize a list to store slashing loss results.

    # Iterate over each state in the scenario to calculate slashing losses.
    for x in range(len(lidoavgbalance)):
        result_list_sl.append(get_exam_slashing(
                scenario[x][2], 
                lidoavgbalance[x]*EFFECTIVE_BALANCE_INCREMENT, 
                lidoavgeffbalance[x]*EFFECTIVE_BALANCE_INCREMENT, 
                validatorscount[x], 
                eligibleether[x]*EFFECTIVE_BALANCE_INCREMENT/validatorscount[x],
                spec = 'Capella'
                )['total_loss'])
    
    result_list = [] # Initialize a list to store offline loss results.

    # Iterate over each state in the scenario to calculate offline losses.
    for x in range(len(lidoavgbalance)):
        if scenario[x][0] ==0: result_list.extend([0])
        else:
            result_list.append(get_exam_offline(
                scenario[x][1]*24*3600/SECONDS_PER_SLOT/SLOTS_PER_EPOCH, 
                scenario[x][0], 
                lidoavgbalance[x]*EFFECTIVE_BALANCE_INCREMENT, 
                lidoavgeffbalance[x]*EFFECTIVE_BALANCE_INCREMENT, 
                validatorscount[x], 
                eligibleether[x]*EFFECTIVE_BALANCE_INCREMENT/validatorscount[x], 
                spec = 'Capella'
                )['total_loss'])
            
    # Create a DataFrame to display the calculated losses.        
    df_result = pd.DataFrame({'loss_slashings':result_list_sl, 'loss_offline': result_list}, index = ['scenario_1', 'scenario_2', 'scenario_3'])
    df_result['total_loss'] = df_result.loss_slashings + df_result.loss_offline
    df_result['lidostakeddeposits'] = [lidostakeddeposits[0], lidostakeddeposits[1], lidostakeddeposits[2]]
    df_result['lido_insurance_fund'] = [lido_insurance_fund[0], lido_insurance_fund[1], lido_insurance_fund[2]]
    df_result['%_of_lido_deposits'] = df_result.total_loss/df_result.lidostakeddeposits*100
    df_result['%_of_lido_funds'] = df_result.total_loss/df_result.lido_insurance_fund*100

    # Print the DataFrame containing the loss results and their impact in percentages.
    pd.options.display.float_format = '{:,.2f}'.format
    print(df_result[['total_loss','loss_slashings', 'loss_offline', '%_of_lido_deposits','%_of_lido_funds']])

def get_scenarios(scenarios):
    for scenario in scenarios:
        print('\n', scenario, ": ", scenarios[scenario][-1])
        print("\nParams")
        index = ['validators offline', 'days offline', 'validators slashed']
        pd.options.display.float_format = '{:,.0f}'.format
        print(pd.concat([pd.DataFrame({'scenario_1':scenarios[scenario][0]},index = index).T,pd.DataFrame({'scenario_2':scenarios[scenario][1]},index = index).T, pd.DataFrame({'scenario_3':scenarios[scenario][2]},index = index).T]))
        scenario_exam = scenarios[scenario]
        print("\nResults")
        get_scenario(scenario_exam)
        print()

def get_results_slashing(exams):
    specs = ['Capella']
    results = [get_result_slashing(exams, state, spec, slashed_validators_porcentage_a, slashed_validators_porcentage_b, slashed_validators_porcentage_c, slashed_validators_porcentage_d) for spec in specs for state in states]
    titles = [(state, spec) for spec in specs for state in states]
    for result in range(len(results)):
        pd.options.display.float_format = '{:,.2f}'.format
        print(titles[result])
        print(results[result])
        print()
    return results

def get_result_slashing(exams, state, spec, slashed_validators_porcentage_a, slashed_validators_porcentage_b, slashed_validators_porcentage_c, slashed_validators_porcentage_d):

    if state == 'scenario_2': x = 1
    elif state == 'scenario_3': x = 2
    else: x = 0

    result_list = [get_exam_slashing(
        exams[y][x], 
        lidoavgbalance[x]*EFFECTIVE_BALANCE_INCREMENT, 
        lidoavgeffbalance[x]*EFFECTIVE_BALANCE_INCREMENT, 
        validatorscount[x], 
        eligibleether[x]*EFFECTIVE_BALANCE_INCREMENT/validatorscount[x], 
        spec
        ) for y in range(len(exams))]

    df_result = pd.DataFrame(
        result_list, 
        index = [
            "{:,.0%}".format(slashed_validators_porcentage_a) + ' total validators slashed',
            "{:,.0%}".format(slashed_validators_porcentage_b) + ' total validators slashed',
            "{:,.0%}".format(slashed_validators_porcentage_c) + ' total validators slashed',
            "{:,.0%}".format(slashed_validators_porcentage_d) + ' total validators slashed'])
    df_result['%_of_lido_deposits'] = df_result.total_loss/lidostakeddeposits[x]*100
    df_result['%_of_lido_funds'] = df_result.total_loss/lido_insurance_fund[x]*100
    return df_result[['total_loss','%_of_lido_deposits','%_of_lido_funds']]

def get_exam_offline(epochs_offline, exam, lidoavgbalance, lidoavgeffbalance, validatorscount, avarage_effective_balance, spec):
    dic = {}
    result = functions.process_offline_validator_Capella(epochs_offline, lidoavgbalance, lidoavgeffbalance, validatorscount, avarage_effective_balance) 
    prob_number_validators_assigned = functions.get_probability_outcomes(exam, validatorscount, 0.99, SYNC_COMMITTEE_SIZE)*result[4]
    dic.update({'offline_count': exam})
    dic.update({'total_loss_offline_penalty': functions.gwei_to_ether((result[0]-lidoavgbalance)*exam)})
    dic.update({'average_loss_offline_penalty': functions.gwei_to_ether(result[0]-lidoavgbalance)})
    dic.update({'total_loss': functions.gwei_to_ether((result[0]-lidoavgbalance)*(exam-prob_number_validators_assigned)+(result[2]-lidoavgbalance)*prob_number_validators_assigned)})
    dic.update({'average_loss': functions.gwei_to_ether(result[2]-lidoavgbalance)})
    return dic

def get_exam_slashing(exam, lidoavgbalance, lidoavgeffbalance, validatorscount, avarage_effective_balance, spec):
    dic = {}
    result = functions.process_slashings_bellatrix(exam, lidoavgbalance, lidoavgeffbalance, validatorscount, avarage_effective_balance)   
    dic.update({'slashings_count': exam})
    dic.update({'total_loss': functions.gwei_to_ether((result[0]-lidoavgbalance)*exam)})
    dic.update({'average_loss': functions.gwei_to_ether(result[0]-lidoavgbalance)})
    return dic

## MAIN
# current state of beacon chain
current_epoch_data = functions.get_epoch_data(functions.get_epoch_data()['epoch']-1)
validatorscount_current = int(current_epoch_data['validatorscount'])
current_epoch = current_epoch_data['epoch']
totalvalidatorbalance_current = current_epoch_data['totalvalidatorbalance']
eligibleether_current = current_epoch_data['eligibleether']
average_effective_balance = eligibleether_current/validatorscount_current

# Lido param
current_lido_deposits = 9326604 # ETH staked
lido_treasury_percentage = 0.80
steth_in_treasury = 36975
dai_in_treasury = 1400000
usdt_in_treasury = 2250000
eth_price = 2600

hedge_fund_scenario_1 = 6287
hedge_fund_scenario_2 = hedge_fund_scenario_1 + steth_in_treasury * lido_treasury_percentage
hedge_fund_scenario_3 = hedge_fund_scenario_2 + (dai_in_treasury + usdt_in_treasury) * lido_treasury_percentage / eth_price

lido_share = current_lido_deposits/functions.gwei_to_ether(current_epoch_data['eligibleether'])

lido_validator_average_eff_balance = MAX_EFFECTIVE_BALANCE
lido_validator_average_balance = 32000000000 #32905178993.948082
period_offline = 256 #epochs
lido_validators = 288000

# params for calculation
validatorscount = np.array([validatorscount_current, validatorscount_current, validatorscount_current])
eligibleether = validatorscount*(functions.gwei_to_ether(average_effective_balance))
lidoshare = [lido_share, lido_share, lido_share]
lido_insurance_fund = [hedge_fund_scenario_1, hedge_fund_scenario_2, hedge_fund_scenario_3]
lidostakeddeposits = [eligibleether[x]*lidoshare[x] for x in range(len(lidoshare))]
lidoavgeffbalance = functions.gwei_to_ether(np.array([lido_validator_average_eff_balance, lido_validator_average_eff_balance, lido_validator_average_eff_balance]))
lidoavgbalance = functions.gwei_to_ether(np.array([lido_validator_average_balance, lido_validator_average_balance, lido_validator_average_balance]))

slashed_validators_porcentage_a = 0.0495
slashed_validators_porcentage_b = 0.1
slashed_validators_porcentage_c = 0.15
slashed_validators_porcentage_d = 0.20

exams = [
    [slashed_validators_porcentage_a * lido_validators, slashed_validators_porcentage_a * lido_validators, slashed_validators_porcentage_a * lido_validators],
    [slashed_validators_porcentage_b * lido_validators, slashed_validators_porcentage_b * lido_validators, slashed_validators_porcentage_b * lido_validators],
    [slashed_validators_porcentage_c * lido_validators, slashed_validators_porcentage_c * lido_validators, slashed_validators_porcentage_c * lido_validators],
    [slashed_validators_porcentage_d * lido_validators, slashed_validators_porcentage_d * lido_validators, slashed_validators_porcentage_d * lido_validators]]

inputdata = {
        'total active validators': validatorscount,
        'total eligible ETH': eligibleether,
        "Lido's share": lidoshare,
        "Lido's deposits": lidostakeddeposits,
        "Lido's reserves": lido_insurance_fund,
        "Average effective balance of validators": lidoavgeffbalance,
        "Average balance of Lido's validators": lidoavgbalance,
        "{:,.0%}".format(slashed_validators_porcentage_a) + ' total validators slashed': exams[0],
        "{:,.0%}".format(slashed_validators_porcentage_b) + ' total validators slashed': exams[1],
        "{:,.0%}".format(slashed_validators_porcentage_c) + ' total validators slashed': exams[2],
        "{:,.0%}".format(slashed_validators_porcentage_d) + ' total validators slashed': exams[3]}
df_inputdata = pd.DataFrame(inputdata).T
df_inputdata.columns=['scenario_1', 'scenario_2', 'scenario_3']

# OUTCOMES
print("\nPARAMS\n")
print(df_inputdata)

# slashing penalties modeling
print("\n\nSLASHING PENALTIES MODELING\n")
get_results_slashing(exams)