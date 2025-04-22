import random, time
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import lognorm
import pandas as pd
import math
from collections import Counter

def sample_damage_InverseTrams(IM_evaluated, CompName, CompFra_dict_input):
    # Return a component damage state (discrete) based on provided IM and componentModelname
    # Frag_set = [(frag_median_M, frag_dispersion_M)]
    
    #--------------------------------------------------
    # Assign the fragility set according to class tag
    #------------------------------------------------
    #- Search the index of the object where the 'Class' key equals to a given bridge classtag
    #index = next((i for i,dct in enumerate(SysFra_dict['BridgeFrag']) if dct['Class'] == classtag),None)
    '''
    if FraRandSampleFlag == 0:
    # =0: do not randomly sample fragility functions from multiple sources. i.e., using the first one provided in the table
    # =1: DO randomly sample fragility functions from multiple sources
        frag_set = SysFra_dict['BridgeFrag'][index]['SysFra'][0]['Fra_Set']
    else:
        frag_set = SysFra_dict['BridgeFrag'][index]['SysFra'][random.randint(0,num_sources-1)]['Fra_Set']
    #print('frag set is',frag_set)
    '''
    rand_num = random.uniform(0, 1)  # Generate a uniformally distributed number
    
    try:
        frag_set = CompFra_dict_input['CompFra'][CompName]
    except: 
        print("CompModelName must be one of the following: ['Col', 'Seat_ab','Super', 'ColFnd', 'AbFnd', 'Backwall', 'Bearing_ab', 'Key_ab','ApproSlab','JointSeal_ab','JointSeal_super', 'Seat_super', 'Bearing_super', 'Key_super']")
    
    prob_exceed = [lognorm.cdf(IM_evaluated, s=dispersion, scale=median) for median, dispersion in frag_set] # Calculate the probability of lognormal at IM
    
    if len(frag_set) == 2:  # Only Slight and Moderate damage states provided
        return 0 if rand_num > prob_exceed[0] else 1 if rand_num > prob_exceed[1] else 2
    elif len(frag_set) == 4:  # All damage states provided
        return (0 if rand_num > prob_exceed[0] else
                1 if rand_num > prob_exceed[1] and rand_num <= prob_exceed[0] else
                2 if rand_num > prob_exceed[2] and rand_num <= prob_exceed[1] else
                3 if rand_num > prob_exceed[3] and rand_num <= prob_exceed[2] else
                4)

    
    
    
def sample_damage_correlated_baker(IM_fixed_input, CompModelName_List_input, CompModelQty_input, 
                                    IntraGroupRule_input, CompFra_dict_input, 
                                   correlation_weight_input, num_rlz_input):
    # Return a component damage state (discrete) based on provided IM and componentModelname
    random.seed(1223)
    np.random.seed(1223)

    #------------Input-----------------------------
    # IM_fixed: scalar
    # CompModelName_List_input: A list containing all CompModelName
    # CompModelQty_input: this indicate the quantity for each CompModelName
    # IntraGroupRule_input: determine what CompModelNames are regarded to be in a same group
    # CompFra_dict_input: A dict with key of each CompName and value the fragility set in the format of [(frag_median_M, frag_dispersion_M)]
    # correlation_weight_input: [w_all, w_sys, w_inde] with these three portions sum up to 1
    # num_rlz_input: scalar
    #------------------------------------------------
    
    #---------- Output-------------------------------
    # DamageSample_CompModel_Qty: Sampled damage tag for each CompModel, distinguishing quantity
    
    CapSample_CompModel_Qty =  {CompModelName:None for CompModelName in CompModelName_List_input} 

    epsilon_intercomp = np.random.normal(0,1,num_rlz_input)   #epsilon_all in Baker

    for sys,subsys_list in IntraGroupRule_input.items():
        #print(f"this is SYSTEM {sys}")
        epsilon_intracomp = np.random.normal(0,1,num_rlz_input)  #epsilon_sys in Baker, #n_CompModel * n_simu 

        for subsys in subsys_list:
            #print(f"this is subsys {subsys}")
            cap_subsys = [] # aggregaing the quantity per subsys
            qty_subsys = CompModelQty_input[subsys]
            #print(f"this quantity is {qty_subsys}")
            num_DS = len(CompFra_dict_input['CompFra'][subsys])

            for qty_idx in range(qty_subsys):
                cap_subsys_qty = np.full((num_DS, num_rlz_input), np.nan) # num_DS * num_simu

                epsilon_inde = np.random.normal(0,1,size=(num_rlz_input)) #epsilon_independent per comp qty

                compVariate_perDS_perCompQty =  ( np.sqrt(correlation_weight_input[0]) * epsilon_intercomp     
                                         +   np.sqrt(correlation_weight_input[1]) *  epsilon_intracomp
                                         +   np.sqrt(correlation_weight_input[2]) * epsilon_inde)

                for DS_idx in range(num_DS):
                    marginal_median_capacity = CompFra_dict_input['CompFra'][subsys][DS_idx][0]
                    #print(marginal_median_capacity)
                    marginal_dispersion = CompFra_dict_input['CompFra'][subsys][DS_idx][1]
                    cap_subsys_qty[DS_idx,:] = np.exp(   np.log(marginal_median_capacity)
                                                   + marginal_dispersion * compVariate_perDS_perCompQty)
                
                cap_subsys.append(cap_subsys_qty)
                # cap_subsys dim: comp qty * num_DS * num_rlz
            CapSample_CompModel_Qty[subsys] = cap_subsys


    # Compare the sampled capacity with the specified IM value (demand) to get the damage
    DamageSample_CompModel_Qty_output =  {CompModelName:None for CompModelName in CompModelName_List_input} 

    t1 = time.time()
    for subsys in CompModelName_List_input:
        Cap_Sample_current = CapSample_CompModel_Qty[subsys]
        qty_subsys = CompModelQty_input[subsys]
        DS_subsys = [] # aggregaing the quantity per subsys

        for qty_idx in range(qty_subsys):
            Cap_Sample_current_qty = Cap_Sample_current[qty_idx]
            num_DS = len(Cap_Sample_current_qty)
            
            '''
            DS_subsys_qty = [None] * (num_rlz_input)
            for rlz_idx in range(num_rlz_input): 
                cap_perobs = Cap_Sample_current_qty[:,rlz_idx]
                DS_perobs = None

                for DS_idx in range(1,num_DS):
                    if cap_perobs[DS_idx-1] <= IM_fixed_input < cap_perobs[DS_idx]:
                        DS_perobs = DS_idx
                        break
                    if (DS_perobs is None) and (IM_fixed_input >= cap_perobs[-1]):
                        DS_perobs = num_DS
                    if (DS_perobs is None) and (IM_fixed_input < cap_perobs[0]):
                        DS_perobs = 0
                DS_subsys_qty[rlz_idx] = DS_perobs # per obs
            '''
            # compare the sampled comp capacity with the given IM demand
            DS_subsys_qty = np.array([np.searchsorted(col, IM_fixed_input, side="left") for col in Cap_Sample_current_qty.T]).tolist()
            DS_subsys.append(DS_subsys_qty) # per qty

        DamageSample_CompModel_Qty_output[subsys] = DS_subsys # per subsys
    t2 = time.time()
    #print(f"Time: {t2 - t1}")

    return DamageSample_CompModel_Qty_output


def formalize_CountDamagedQty(CompName_List_input,DamageSample_Comp_Qty_input):
    ##---- Convert 'DamageSample_Comp_Qty' (sampled scattered DS per qty, per rlz) into a count dict 'CountDamagedQty' (per rlz, per DS )
    CountDamagedQty = {CompName1: None for CompName1 in CompName_List_input}

    for CompName1 in CountDamagedQty.keys():
        DamageSample_perqty_this = DamageSample_Comp_Qty_input[CompName1]
        DamageSample_perrlz_this = list(zip(*DamageSample_perqty_this))
        if (CompName1 == 'Col') or ('seat' in CompName1.lower()): # if CompName1 is a primary component
            num_allDS_this = 4
        else:
            num_allDS_this = 2

    # Creating a list with multiple tuples (totals # of simu), each tuple counts how many components fall in a specific DS. 
    # Structure -  count_DS_Col = [ ( # of columns fall in DS0,  # of columns fall in DS1, ... # of columns fall in DS4), (counts of the 2nd MCS),...]
        count_DS_this = []
        for DSSample_perrlz_tuple in DamageSample_perrlz_this:
            DStag_counts = Counter(DSSample_perrlz_tuple)
            count_DS_this_rlz = tuple(DStag_counts.get(ds,0) for ds in range(num_allDS_this+1)) # Ensuring that each possible damage state is represented, even if its count is 0
            count_DS_this.append(count_DS_this_rlz)

        CountDamagedQty[CompName1] = count_DS_this

    return CountDamagedQty



def map_comp_RC(count_DS_comp_input, CompName_input):
    # Return a list 'RC_assigned_comp' (for a component type) containing the mapped RC per rlz     
    #--------------------------------------------------
    #- count_DS_comp_input: a list (from its parent dict 'CountDamagedQty') that contains multiple tuples. Each tuple means the count of comps (totals qty_comp) falling into a speific DS per rlz.
    #- RC_Rule_input: Rule (a list from the dict 'RC_List') defines the maping from component damage and associated quantity to a RC
    num_rlz = len(count_DS_comp_input)
    CompQty = sum(count_DS_comp_input[0])

    RC_assigned_comp = []
    if (CompName_input == 'Col') or ('seat' in CompName_input.lower()): # if CompName1 is a primary component
        # check if primary components have 5 DSs
        if len(count_DS_comp_input[0]) != 5:
            raise ValueError(f"The number of DSs for {count_DS_comp_input} (primary) is not equal to 5.")

        for rlz_idx in range(num_rlz):
            DScount_List = count_DS_comp_input[rlz_idx]
            # at least one in DS4 OR > 50% in DS3 --> RC5
            if (DScount_List[4] >= 1) or (DScount_List[3] > .5 * CompQty):
                RC_assigned_comp.append(5)
            # > 50% in DS2 OR at least one but <= 50% in DS3 --> RC4
            elif (DScount_List[2] >  .5 * CompQty) or (  (DScount_List[3] >=1 )   and (DScount_List[3] <= .5 * CompQty)  ):
                RC_assigned_comp.append(4)
            # > 50% in DS1 OR at least one but <50% in DS2 --> RC3
            elif (DScount_List[1] > .5 * CompQty) or (  (DScount_List[2] >=1 )   and (DScount_List[2] <= .5 * CompQty)  ):
                RC_assigned_comp.append(3)
            # At least one but <= 50% in DS1 --> RC2
            elif (  (DScount_List[1] >=1 )   and (DScount_List[1] <= .5 * CompQty)  ):
                RC_assigned_comp.append(2)
            # all in DS0 --> RC1
            elif ( DScount_List[0] == CompQty ):
                RC_assigned_comp.append(1)
            else:
                raise ValueError(f"RC Assignment Wrong in {CompName_input}")


    else: # secondary componnet
        # check if secondary components have 3 DSs
        if len(count_DS_comp_input[0]) != 3:
            raise ValueError(f"The number of DSs for {count_DS_comp_input} (secondary) is not equal to 3.")

        for rlz_idx in range(num_rlz):
            DScount_List = count_DS_comp_input[rlz_idx]

            # at least one in DS2  --> RC3
            if (DScount_List[2] >= 1):
                RC_assigned_comp.append(3)
            # at least one in DS1 AND None in DS2 --> 
            elif (DScount_List[1] >= 1) and (DScount_List[2] == 0):
                RC_assigned_comp.append(2)
            # all in DS0 --> RC1
            elif (DScount_List[0] == CompQty ):
                RC_assigned_comp.append(1)
            else:
                raise ValueError(f"RC Assignment Wrong in {CompName_input}")


    
    return RC_assigned_comp # a list containing assigned RC per rlz



    '''
    totqty_comp = sum(count_DS_comp_input[0])
    DS_num = len(count_DS_comp_input[0]) # num of possible DS's for this component, including DS0 (No-damage)
    
    RC_Rule_input_adj = [] # create a new one to avoid hard copy 
    # ---------------------------------------------------------------------
    # Convert 'proportion' specified in the mapping rule into real number
    for idx, RC_Rule_input_DS in enumerate(RC_Rule_input):
        RC_options, qty_options = RC_Rule_input_DS # lists
        # We adjust the values in qty_options to ensure: (1) if qty <1, it means it is a proporiton of tot qty, instead of a real number
        # so we convert that to real number by rounding down (with conservativeness ).
        # (2) the values in the adjusted qty_option should always be larger or equal to their predecessors
        
        qty_options_adj0 = [ (max(qty * totqty_comp,1) if 0< qty < 1 else qty  ) for qty in qty_options]
        qty_options_adj = [max(qty_options_adj0[:qty_idx+1]) for qty_idx in range(len(qty_options_adj0))]
        RC_Rule_input_adj.append(tuple([RC_options,qty_options_adj]))
    #print(RC_Rule_input_adj)
    #--------------------------------------------------------------------------
    
    # ---------------------------------------------------------------------
    # Start to map RC for each rlz 
    RC_assigned_comp = []
    for idx_rlz, count_DS_comp_input_rlz in enumerate(count_DS_comp_input): # count per rlz
        RC_assigned = 1 # by default it is assigned as 1 if no conditions are met
        
        for idx, (RC_opts, min_qtys) in enumerate(reversed(RC_Rule_input_adj),start = 1): # per DS
            DS = DS_num - idx # the current DS. Since we use reversed, convert it. 
            count_thisDS = count_DS_comp_input_rlz[DS]
            
            # Now, compare the current count (under a DS and within a rlz) with the min_qty (reversed order)
            for RC_opt_scalar, min_qty_scalar in zip(reversed(RC_opts), reversed(min_qtys)): # per RC option
                if count_thisDS >= min_qty_scalar:
                    RC_assigned = RC_opt_scalar
                    
                    break # beark the count-minQty comparison for-loop
            
            if RC_assigned!=1:
                break # break the DS for-loop
                
        RC_assigned_comp.append(RC_assigned)
    return RC_assigned_comp # a list containing assigned RC per rlz
    '''


'''
def sample_order_IF(sysDS_rlz_input, Impeding_dataset_input, emergency_protocol_flag):
    # emergency_protocol_flag=1 means it is triggered
    IF_sampled_list_output = {key: [None]*len(sysDS_rlz_input) for key in Impeding_dataset_input[1]}
    IF_sum_list_output = [None]*len(sysDS_rlz_input)

    random.seed(1223)
    np.random.seed(1223)

    for SysDS_idx, SysDS in enumerate(sysDS_rlz_input):
        if SysDS not in range(0,5):
            raise ValueError("SysDS not in [0,4]")
        elif SysDS == 0: # system no damage
            IF_sum_list_output[SysDS_idx] = 0       
            for IFName,_ in Impeding_dataset_input[1].items():
                IF_sampled_list_output[IFName][SysDS_idx] = 0
        else:    
            #Sampling individual impeding factors 
            for IFName,bounds in Impeding_dataset_input[SysDS].items():
                lower_bound, upper_bound = bounds
                IF_sampled_list_output[IFName][SysDS_idx] = random.uniform(lower_bound, upper_bound)

            # The triggering probability of permitting is 30%
            if (np.random.uniform(0, 1) > .3):
                IF_sampled_list_output['Permitting'][SysDS_idx] = 0

            # The triggering probability of in-depth inspection dependes on sysDS
            if (SysDS == 0 or 4): threshold = 0
            if (SysDS == 1): threshold = .1
            if (SysDS == 2): threshold = 1
            if (SysDS == 3): threshold = .6   

            if (np.random.uniform(0, 1) > threshold):
                IF_sampled_list_output['InDepInsp'][SysDS_idx] = 0

            #Order the sampled impeding factors and calculate the sum
            if SysDS in [1,2]: # Sequencing under non-emergency response
                IF_sum_list_output[SysDS_idx] = IF_sampled_list_output['IniInsp'][SysDS_idx] + IF_sampled_list_output['InDepInsp'][SysDS_idx]+ max(IF_sampled_list_output['Financing'][SysDS_idx], IF_sampled_list_output['Contractor'][SysDS_idx], IF_sampled_list_output['Design'][SysDS_idx]+IF_sampled_list_output['Permitting'][SysDS_idx])
            elif SysDS in [3,4]: # Sequencing under emergency response
                IF_sum_list_output[SysDS_idx] = IF_sampled_list_output['IniInsp'][SysDS_idx] + IF_sampled_list_output['InDepInsp'][SysDS_idx]+ max(IF_sampled_list_output['Financing'][SysDS_idx], IF_sampled_list_output['Design'][SysDS_idx]+IF_sampled_list_output['Contractor'][SysDS_idx] +IF_sampled_list_output['Permitting'][SysDS_idx])

    return IF_sampled_list_output,IF_sum_list_output
'''
def sample_order_IF(sysDS_rlz_input, Impeding_dataset_input, emergency_protocol_flag_input):
    # emergency_protocol_flag=1 means it is triggered
    IF_sampled_list_output = {key: [None]*len(sysDS_rlz_input) for key in Impeding_dataset_input.keys()}
    IF_sum_list_output = [None]*len(sysDS_rlz_input)

    random.seed(1223)
    np.random.seed(1223)

    for SysDS_idx, SysDS in enumerate(sysDS_rlz_input):
        if SysDS not in range(0,5):
            raise ValueError("SysDS not in [0,4]")
        elif SysDS == 0: # system no damage
            IF_sum_list_output[SysDS_idx] = 0       
            for IFName,_ in Impeding_dataset_input.items():
                IF_sampled_list_output[IFName][SysDS_idx] = 0
        else:    
            #Sampling individual impeding factors 
            for IFName,bounds_list in Impeding_dataset_input.items():
                # EP not triggered, not affect functionality 
                if SysDS in [0,1] and emergency_protocol_flag_input[SysDS_idx]!=1:
                    lower_bound, upper_bound = bounds_list[0]
                #EP not triggered, affect functionality
                elif SysDS in [2,3,4] and emergency_protocol_flag_input[SysDS_idx]!=1:
                    lower_bound, upper_bound = bounds_list[1]
                #EP triggered, bridge not in complete DS
                elif SysDS in [2,3] and emergency_protocol_flag_input[SysDS_idx]==1:
                    lower_bound, upper_bound = bounds_list[2]
                # EP triggered, bridge in complete DS
                elif SysDS ==4 and emergency_protocol_flag_input[SysDS_idx]==1:
                    lower_bound, upper_bound = bounds_list[3]

                IF_sampled_list_output[IFName][SysDS_idx] = random.uniform(lower_bound, upper_bound)

            # The triggering probability of permitting is 30%
            if (np.random.uniform(0, 1) > .3):
                IF_sampled_list_output['Permitting'][SysDS_idx] = 0

            # The triggering probability of in-depth inspection dependes on sysDS
            if (SysDS == 0 or 4): threshold = 0
            if (SysDS == 1): threshold = .1
            if (SysDS == 2): threshold = 1
            if (SysDS == 3): threshold = .6   

            if (np.random.uniform(0, 1) > threshold):
                IF_sampled_list_output['InDepInsp'][SysDS_idx] = 0

            #Order the sampled impeding factors and calculate the sum
            if emergency_protocol_flag_input[SysDS_idx]!=1: # Sequencing under non-emergency response
                IF_sum_list_output[SysDS_idx] = IF_sampled_list_output['IniInsp'][SysDS_idx] + \
                IF_sampled_list_output['InDepInsp'][SysDS_idx]+\
                max(IF_sampled_list_output['Financing'][SysDS_idx], IF_sampled_list_output['Contractor'][SysDS_idx]+IF_sampled_list_output['Design'][SysDS_idx]+IF_sampled_list_output['Permitting'][SysDS_idx])
           
            else: # Sequencing under emergency response
                IF_sum_list_output[SysDS_idx] = IF_sampled_list_output['IniInsp'][SysDS_idx] + \
                IF_sampled_list_output['InDepInsp'][SysDS_idx]+\
                max(IF_sampled_list_output['Contractor'][SysDS_idx], IF_sampled_list_output['Permitting'][SysDS_idx]+IF_sampled_list_output['Design'][SysDS_idx])

    return IF_sampled_list_output,IF_sum_list_output


def sample_replacementdur(Worker_Replace_input,repldur_min_input,repldur_max_input,replworker_max_input, replworker_min_input, 
                          WorkHour_input,
                          num_concrete_pour_input, # each concrete pout corresponding to an addition of a 28-day curing time
                          dispersion_assigned_scalar):
    
    random.seed(1223)
    np.random.seed(1223)
   
    # Interpolate the median dur for the bridge replacement
    if Worker_Replace_input< replworker_min_input: raise ValueError("The provided worker number does not satisfy the minimum req");
    elif Worker_Replace_input>= replworker_max_input: med_repl_dur = repldur_min_input;
    else: med_repl_dur = np.interp(Worker_Replace_input, [replworker_min_input, replworker_max_input], [repldur_max_input, repldur_min_input])

    Replace_Dur_Sampled = np.random.lognormal(mean=np.log(med_repl_dur),sigma=dispersion_assigned_scalar,size=1)[0]
    #consider extended work hour
    if WorkHour_input<8 or WorkHour_input>24:
        raise ValueError("WorkHour_input must be in between 8 and 24")
    else:
        Replace_Dur_Sampled = Replace_Dur_Sampled * (8/WorkHour_input)
    
    Replace_Dur_Sampled = Replace_Dur_Sampled + num_concrete_pour_input*28
    return(Replace_Dur_Sampled)



def sample_comp_repairdur_old(DS_comp_rlz,RepDur_comp_dict_input, RepDur_WorkerBound_dict_input, WorkerAllo_Comp_input, ConcreteCuringTime_comp_dict_input, dispersion_assigned_scalar):
    #--- Updated, Oct7, 2024
    #--- One mistake in the previous version is we sum up concrete curing time for each damaged component
    #--- In this version, the curing time only need to be add once, if multiple components within a type are damaged
    #--- Input
    #    DS_comp_rlz: a dict containing the sampled DS per rlz (i.e., a column in 'DamageSample_Comp_Qty'). The length of each value = its quantity
    #    RepDur_comp_dict_input: Min and Max median rep duration for each comp under each DS, including conrete curing time
    #    RepDur_WorkerBound_dict_input: Max and Min worker assigned to each component
    #    WorkerAllo_Comp_input: how many workers are assigned to this component
    #    ConcreteCuringTime_comp_dict_input: what component and under what DS, what's the concrete curing time
    #    dispersion_assigned
    RepDur_sampled_dict = {CompName:None for CompName in DS_comp_rlz} # initiate the sampled rep dur dict
    for CompName, DS_list_perCompType in DS_comp_rlz.items():
        #print(CompName)

        HasConcCureTimeAdded = 0 # A tag to record if the concrete curing time has been added. One comp type can only add once.
        RepDur_comp = 0
        for DS_perComp in DS_list_perCompType:
            print(f"This is DS_perComp {DS_perComp} for {CompName}")

            if DS_perComp == 0:
                RepDur_comp+=0
            else:
                # check if contains concrete curing time
                concrete_curing_time = ConcreteCuringTime_comp_dict_input[CompName][DS_perComp]
                # Read the bounds of median durations for this comp under this DS_perComp
                dur_min,dur_max = RepDur_comp_dict_input[CompName][DS_perComp]
                # exclude concrete during time
                dur_min,dur_max  = dur_min - concrete_curing_time ,dur_max  - concrete_curing_time
                # Read the bounds of worker
                worker_max, worker_min = RepDur_WorkerBound_dict_input[CompName][DS_perComp]
                # Interpolate the median dur for this comp under this DS_perComp
                worker_assigned_comp = WorkerAllo_Comp_input[CompName]
                #print(f"# of workers assigned for {CompName} is {worker_assigned_comp}")
                if worker_assigned_comp< worker_min: raise ValueError(f"The provided worker number does not satisfy the minimum req in comp {CompName}");
                elif worker_assigned_comp>=worker_max: med_dur = dur_min;
                else: med_dur = np.interp(worker_assigned_comp, [worker_min, worker_max], [dur_max, dur_min])
                # Sample from lognormal
                dur_sampled = np.random.lognormal(mean=np.log(med_dur),sigma=dispersion_assigned_scalar)
                RepDur_comp += dur_sampled
                #print(f"Sampled Dur for this single {CompName} is {dur_sampled}")
                if (concrete_curing_time > 0) & (HasConcCureTimeAdded == 0 ):
                    #print(f"{CompName}, DS_perComp = {str(DS_perComp)}, add concrete curing time {concrete_curing_time}")
                    RepDur_comp += concrete_curing_time
                    HasConcCureTimeAdded= 1

        RepDur_sampled_dict[CompName] = RepDur_comp
        #print(f"Sampled Dur summing over all quantities for {CompName} is {RepDur_comp}")
    return RepDur_sampled_dict


def assign_comprep_to_crew(rep_dur_percomp, num_crew_percomptype, compname):
    # a function to calculate comp type-level repair duration, 
    # accounting for number of cews assigned to each component type
    # the load assignment is based on the min. total time each cew undertake 

    #- input
    # rep_dur_percomp: a list, containing the rep duration for each comp within this comp type. Number of workers within each cew has been accounted for.
    # num_crew_percomptype: a scalar
    # compname: name of the current component type
    
    #- output
    # max(crew_load): the max time among the crews undertake
    
    if num_crew_percomptype<=0:
        raise ValueError(f"The assigned work crew number {num_crew_percomptype} for {compname} is <= 0")
    
    rep_dur_percomp = [t for t in rep_dur_percomp if t > 0]
    rep_dur_percomp.sort(reverse=True) # Sort tasks in descending order
    
    # Initialize crew workloads
    crew_load = [0] * num_crew_percomptype
    
    # Distribute per-component tasks to the least loaded crew
    for t in rep_dur_percomp:
        least_loaded = crew_load.index(min(crew_load))
        crew_load[least_loaded] += t
    #print(crew_load)
    
    # The total time will be the maximum load among the crews
    return max(crew_load)


def sample_comp_repairdur(DS_comp_rlz,RepDur_comp_dict_input, RepDur_WorkerBound_dict_input, 
                               WorkerAllo_Comp_input, NumCrew_percomp_input, WorkHour_input,
                               ConcreteCuringTime_comp_dict_input, ColSuperMatType_input,
                               dispersion_assigned_scalar):
    #--- Updated, Jan4, 2025
    #--- Incoporate worker crew that accounts for repairing multiple damaged components in parallel, and multuple work shift. 
    #--- Input
    #    DS_comp_rlz: a dict containing the sampled DS_perComp per rlz (i.e., a column in 'DamageSample_Comp_Qty'). The length of each value = its quantity
    #    RepDur_comp_dict_input: Min and Max median rep duration for each comp under each DS_perComp, including conrete curing time
    #    RepDur_WorkerBound_dict_input: Max and Min worker assigned to each component
    #    WorkerAllo_Comp_input: how many workers are assigned per cew, per component
    #    NumCrew_percomp_input: how many crews are assigned for each comp
    #    WorkHour_input: between 8 to 24; how many work hours per day. 
    #    ConcreteCuringTime_comp_dict_input: what component and under what DS_perComp, what's the concrete curing time
    #    ColSuperMatType_input: a dict containing limited components indicating whether it is made of concrete. If not, then (a) it is in DS 3 (extensive), repair duration cut-down by 50%, and (b) elimate concrete curing time
    #    dispersion_assigned

    RepDur_sampled_dict = {CompName:None for CompName in DS_comp_rlz} # initiate the sampled rep dur dict
    for CompName, DS_list_perCompType in DS_comp_rlz.items():

        RepDur_percomp = [None] * len(DS_list_perCompType); # iniailize the repair duration vector recording sampled dur for each comp within this comp type

        # iterater over all DSs for this comptype, and obtain a vector '' recording time needed to repair each component 'RepDur_percomp' within this type
        for DS_idx, DS_perComp in enumerate(DS_list_perCompType):
            #print(f"This is DS_perComp {DS_perComp} for {CompName}")
            
            if DS_perComp == 0:
                RepDur_percomp[DS_idx] = 0
            else:
                # Read the bounds of median durations for this comp under this DS_perComp
                dur_min,dur_max = RepDur_comp_dict_input[CompName][DS_perComp]
                # exclude concrete curing time from repair duration
                concrete_curing_time = ConcreteCuringTime_comp_dict_input[CompName][DS_perComp]
                dur_min,dur_max  = dur_min - concrete_curing_time ,dur_max  - concrete_curing_time
                # Read the bounds of worker
                worker_max, worker_min = RepDur_WorkerBound_dict_input[CompName][DS_perComp]
                # Interpolate the median dur for this comp under this DS_perComp
                worker_assigned_comp = WorkerAllo_Comp_input[CompName]
                #print(f"# of workers assigned for {CompName} is {worker_assigned_comp}")
                if worker_assigned_comp< worker_min: raise ValueError(f"The provided worker number does not satisfy the minimum req in comp {CompName}");
                elif worker_assigned_comp>=worker_max: med_dur = dur_min;
                else: med_dur = np.interp(worker_assigned_comp, [worker_min, worker_max], [dur_max, dur_min])


                # Sample from lognormal
                dur_sampled = np.random.lognormal(mean=np.log(med_dur),sigma=dispersion_assigned_scalar)
                #consider extended work hour
                if WorkHour_input<8 or WorkHour_input>24:
                    raise ValueError("WorkHour_input must be in between 8 and 24")
                else:
                    dur_sampled = dur_sampled * (8/WorkHour_input)
                    
                RepDur_percomp[DS_idx] = dur_sampled
                

        # Using load-balancing scheduling to assign component-level repairs based on the least loaded work when multiple work crews are invovled for each comp type 
        num_crew_thiscomptype = NumCrew_percomp_input[CompName]
        # if the component is not made of concrete, cut off the repair time by a half to account for time saving from place rebar, install form, and pour concrete
        if CompName in ColSuperMatType_input.keys(): 
            if 'concrete' not in (ColSuperMatType_input[CompName].lower()): # not made of concrete
                # for column in DS 3 that not made of concrete (require replacement of column), cut down the repair time by a half
                DS3_index = [DS_list_perCompType[i]==3 for i in range(len(DS_list_perCompType))]
                RepDur_percomp_np = np.array(RepDur_percomp)
                RepDur_percomp_np[DS3_index] = RepDur_percomp_np[DS3_index]/2
                RepDur_percomp = RepDur_percomp_np.tolist()
                #if sum(DS3_index) >0:
                #    print(f"{CompName} in DS {max(DS_list_perCompType)} is not made of concrete")
        # obain the total workload that takes the max. time among all work crew chains        
        RepDur_AddWorkCrew_percomptype = assign_comprep_to_crew(RepDur_percomp, num_crew_thiscomptype, CompName)

        # Add concrete curing time
        max_cure_time_thiscomptype = max(ConcreteCuringTime_comp_dict_input[CompName][i] for i in DS_list_perCompType)
        # if the component is not made of concrete, exclude concrete curing time
        if CompName in ColSuperMatType_input.keys(): 
            if 'concrete' not in (ColSuperMatType_input[CompName].lower()): # not made of concrete
                max_cure_time_thiscomptype = 0 # also, exclude concrete curing time. 

        RepDur_sampled_dict[CompName] = RepDur_AddWorkCrew_percomptype + max_cure_time_thiscomptype
        #print(f"Sampled Dur summing over all quantities for {CompName} is {RepDur_AddWorkCrew_percomptype}")
    
    return RepDur_sampled_dict

'''
def order_comp_repairdur_old(RepDur_sampled_dict,abut_type_string):
    repdur_sum = None
    
    if abut_type_string not in ['Seat','Diaphragm']:
        raise ValueError("abut_type not in Seat or Diaphragm")

    elif abut_type_string == 'Seat':           
        dur_seq1 = RepDur_sampled_dict['Fnd'] + RepDur_sampled_dict['Col'] +RepDur_sampled_dict['Super']
        dur_seq3 = RepDur_sampled_dict['AbPile'] + RepDur_sampled_dict['Seat'] + \
            max(RepDur_sampled_dict['Backwall'] , RepDur_sampled_dict['Key'] , RepDur_sampled_dict['Bearing']) + \
            RepDur_sampled_dict['ApproSlab'] + RepDur_sampled_dict['JointSeal']
        repdur_sum = max(dur_seq1,dur_seq3)
    
    #elif abut_type_string == 'Diaphragm':   
    #    dur_seq1 = RepDur_sampled_dict['Fnd'] + RepDur_sampled_dict['Col'] +RepDur_sampled_dict['Super']
    #    dur_seq2 = RepDur_sampled_dict['ApproSlab']
    #    dur_seq3 = RepDur_sampled_dict['AbPile'] +  RepDur_sampled_dict['Backwall']
    
    return repdur_sum
'''

def order_comp_repairdur(RepDur_sampled_dict,CompName_List_input):
    repdur_sum = None

    # RepDur_sampled_dict only contains non-empty entris in CompName_List_input
    # update this dict to include all keys in CompName_List_input with those missings with value of 0
    for CompName in CompName_List_input:
        if CompName not in RepDur_sampled_dict:
            RepDur_sampled_dict[CompName] = 0

    # Chain bottom: abutment
    dur_chain_abut = RepDur_sampled_dict['AbFnd'] + RepDur_sampled_dict['Seat_ab'] + \
                max(RepDur_sampled_dict['Backwall'], RepDur_sampled_dict['Key_ab'], RepDur_sampled_dict['Bearing_ab']) + \
                RepDur_sampled_dict['ApproSlab'] + RepDur_sampled_dict['JointSeal_ab']

    # Chain top: substructure - superstructure   
    dur_seat = RepDur_sampled_dict['AbFnd'] + RepDur_sampled_dict['Seat_ab']
    dur_bearing = RepDur_sampled_dict['ColFnd'] + RepDur_sampled_dict['Col'] + \
                max(RepDur_sampled_dict['Bearing_super'], RepDur_sampled_dict['Key_super']) 
    
    dur_chain_super = max(dur_seat, dur_bearing) + \
                RepDur_sampled_dict['Super'] + RepDur_sampled_dict['Seat_super'] + RepDur_sampled_dict['JointSeal_super']
    

    repdur_sum = max(dur_chain_abut,dur_chain_super)
    
    return repdur_sum


'''
def decisiontree_reopeningFS_old(RC_comp_this, RepDur_sampled_this, abut_type_string, FS_rlz_this,
                              DecTreeProb_SuperAppro_input = [.2,.1,.7], DecTreeProb_AbutRelated_input = [.6,.2,.2]):
    # RC_comp_this: a dict of mapped repair class per rlz (i.e., a column in 'RepairCalss_dict'). 
    # RepDur_sampled_this: a dict of sampled rep duration per rlz from 'RepDur_sampled_comp_rlz'
    # Return: a scalar RFS tag
    if abut_type_string not in ['Seat','Diaphragm']:
        raise ValueError("abut_type not in Seat or Diaphragm")

    elif RepDur_sampled_this == 'Complete':
        return FS_rlz_this #return RFS5 - Maintain the Previous Closure Decision
        #print("Since bridge is in complete DS, return previous closure decision")

    elif abut_type_string == 'Seat':     
        # Create a Remaining Secondary Component list that are repaired after primary componens are repaired
        RemCompList = ['Super','Backwall','Bearing','Key']
        if RepDur_sampled_this['JointSeal'] > RepDur_sampled_this['Seat']:
            RemCompList.append('JointSeal')
        if RepDur_sampled_this['ApproSlab'] > RepDur_sampled_this['Seat']:
            RemCompList.append('ApproSlab')
        #print(RemCompList)

        # -- ANY primary component in RC=5 or ALL primary components in RC = 1 or 2, Maintain the Previous Closure Decision
        if (any(rc_val in [5] for rc_val in [RC_comp_this['Col'], RC_comp_this['Seat']]) ) or (all(rc_val in [1,2] for rc_val in [RC_comp_this['Col'], RC_comp_this['Seat']])):
            #print("all components in RC5 or any remaining secondary component in RC1 or 2, return previous closure decision")
            return FS_rlz_this #return: Maintain the Previous Closure Decision
        # all RCs for the remaining second. componts are in RC1 assign - FS1: Fully Repaired
        elif (all(RC_comp_this.get(RemCompName) in [1] for RemCompName in RemCompList)): 
            #print("remaining second. componts are in RC1 , return FS=1")
            return 0 #return FS0: Fully Repaired
        elif (all(RC_comp_this.get(RemCompName) in [1,2] for RemCompName in RemCompList)): 
            #print("remaining second. componts are in RC2 , return FS=2")
            return 1 #return FS1: Fully Functional
        # if Super OR ApproSlab in RC3 
        elif (any(RC_comp_this.get(RemCompName) in [3] for RemCompName in ['Super','ApproSlab'])):
            #print(" Super OR ApproSlab in RC3 ")
            return(np.random.choice([4,5,6], size=1, p=DecTreeProb_SuperAppro_input)[0]) # return: either one in FS4 - Reopen with Weight Restriction, FS5: Reopen with Minor Lane Closure, and FS6: Reopen with Weight Restrictions and Minor Lane Closure
        #if any abut-related comp in RC3
        elif (any(RC_comp_this.get(RemCompName) in [3] for RemCompName in ['Backwall','Bearing','Key','JointSeal'])):
            #print(" any abut-related comp in RC3 ")
            return(np.random.choice([4,5,6], size=1, p=DecTreeProb_AbutRelated_input)[0])
        else:
            raise ValueError("There's some event not considered in this function")

    elif abut_type_string == 'Diaphragm':   
        RemCompList = ['Super']
        if RepDur_sampled_this['ApproSlab'] > RepDur_sampled_this['Col']:
            RemCompList.append('ApproSlab')
        if RepDur_sampled_this['Backwall'] > RepDur_sampled_this['Col']:
            RemCompList.append('Backwall')
        #print(RemCompList)

         # -- if ANY primary component in RC=5 or ALL primary components in RC = 1 or 2
        if (any(rc_val in [5] for rc_val in [RC_comp_this['Col']]) )or (all(rc_val in [1,2] for rc_val in [RC_comp_this['Col']])):
            return FS_rlz_this #Maintain the Previous Closure Decision
        # all RCs for the remaining second. componts are in RC1 assign - FS1: Fully Repaired
        elif (all(RC_comp_this.get(RemCompName) in [1] for RemCompName in RemCompList)): 
            return 0 #return FS0: Fully Repaired
        # all RCs for the remaining second. componts are in RC2 assign - FS2: Fully Functional
        elif (all(RC_comp_this.get(RemCompName) in [1,2] for RemCompName in RemCompList)): 
            return 1 #return FS1: Fully Functional
        # if Super OR ApproSlab in RC3 
        elif (any(RC_comp_this.get(RemCompName) in [3] for RemCompName in ['Super','ApproSlab'])): 
            return(np.random.choice([4,5,6], size=1, p=DecTreeProb_SuperAppro_input)[0])
        #if any abut-related comp in RC3
        elif (any(RC_comp_this.get(RemCompName) in [3] for RemCompName in ['Backwall'])): 
            return(np.random.choice([4,5,6], size=1, p=DecTreeProb_AbutRelated_input)[0])
        else:
            raise ValueError("There's some event not considered in this function")   
'''

def decisiontree_reopeningFS(RC_comp_this, RepDur_sampled_this, FS_rlz_this,
                              DecTreeProb_SuperAppro_input = [.2,.1,.7], DecTreeProb_AbutRelated_input = [.6,.2,.2]):
    # RC_comp_this: a dict of mapped repair class per rlz (i.e., a column in 'RepairCalss_dict'). 
    # RepDur_sampled_this: a dict of sampled rep duration per rlz from 'RepDur_sampled_comp_rlz'
    #-Output:
    # FS_rlz_this: a scalar of functionality state at the reopning phase
    # ReopeningTriggeringFlag: whether the Reopening phase is triggered or not
    random.seed(1223)
    np.random.seed(1223)

    primary_comp_names = ['Col', 'Seat_ab', 'Seat_super']
    RC_primarycomp_this = {key: RC_comp_this[key] for key in RC_comp_this.keys() if key in primary_comp_names}
    RC_secondarycomp_this = {key: RC_comp_this[key] for key in RC_comp_this.keys() if key not in primary_comp_names}
    RC_remaining = {key: RC_secondarycomp_this[key] for key in RC_secondarycomp_this.keys() if key not in ['ColFnd', 'AbFnd']} # preclude foundations

    # - Determine if Reopneing phase is needed
    # - if all of the three conditions are satified, reopening phase is needed
    # - (1) at least one primary component is in RC3 or higher
    # - (2) after one primary components are in RC3, after all primary components are repaired 
    # - (3) bridge is repariable
    
    if RepDur_sampled_this == 'Complete':
        ReopeningTriggeringFlag = 0
        return (FS_rlz_this,ReopeningTriggeringFlag) # Maintain the Previous Closure Decision
        #print("Since bridge is in complete DS, return previous closure decision")

    else:
        # Create a Remaining Secondary Component list that are repaired after primary componens are repaired
        RemCompList_super = ['Super','Bearing_super','JointSeal_super', 'ApproSlab', 'Key_super']
        RemCompList_ab = ['Backwall', 'Bearing_ab', 'Key_ab', 'JointSeal_ab']
        RemCompList_super = list(set(RC_remaining.keys()).intersection(RemCompList_super))
        RemCompList_ab = list(set(RC_remaining.keys()).intersection(RemCompList_ab))
        RC_remaining_super = {key: RC_remaining[key] for key in RC_remaining.keys() if key in RemCompList_super}
        RC_remaining_ab = {key: RC_remaining[key] for key in RC_remaining.keys() if key in RemCompList_ab}
        #print(RC_remaining_super)
        #print(RC_remaining_ab)

        # -- ANY primary component in RC=5 or ALL primary components in RC = 1 or 2, Maintain the Previous Closure Decision
        if ( any(rc_val == 5 for rc_val in RC_primarycomp_this.values())) or (all(rc_val in {1,2} for rc_val in RC_primarycomp_this.values())):
            #print("all components in RC5 or any remaining secondary component in RC1 or 2, return previous closure decision")
            ReopeningTriggeringFlag = 0
            return (FS_rlz_this, ReopeningTriggeringFlag) #return: Maintain the Previous Closure Decision
        
        # all RCs for the remaining second. componts are in RC1 assign - FS1: Fully Functional
        elif (all(rc_val == 1 for rc_val in RC_remaining.values())): 
            #print("remaining second. componts are in RC1 , return FS=1")
            ReopeningTriggeringFlag = 0
            return (0, ReopeningTriggeringFlag) #return FS0: Fully Repaired
        
        # all RCs for the remaining second. componts are in RC 1 or 2 assign - FS1: Fully Functional
        elif (all(rc_val in {1,2} for rc_val in RC_remaining.values())): 
            #print("remaining second. componts are in RC2 , return FS=2")
            ReopeningTriggeringFlag = 0
            return (1, ReopeningTriggeringFlag) #return FS1: Fully Functional
        
        # if Superstructure-related components in RC3 
        elif (any(rc_val == 3 for rc_val in RC_remaining_super.values())):
            #print("  Superstructure-related components in RC3 ")
            ReopeningTriggeringFlag = 1
            return(int(np.random.choice([4,5,6], size=1, p=DecTreeProb_SuperAppro_input)[0]), ReopeningTriggeringFlag) # return: either one in FS4 - Reopen with Weight Restriction, FS5: Reopen with Minor Lane Closure, and FS6: Reopen with Weight Restrictions and Minor Lane Closure
        
        #if any abut-related comp in RC3
        elif (any(rc_val == 3 for rc_val in RC_remaining_ab.values())):
            #print(" any abut-related comp in RC3 ")
            ReopeningTriggeringFlag = 1
            return(int(np.random.choice([4,5,6], size=1, p=DecTreeProb_AbutRelated_input)[0]), ReopeningTriggeringFlag)
        else:
            raise ValueError("There's some event not considered in this function")

            
def rd_num_byMean(percent, lane_before, size=1):
    # this fun is used for generating a closed lane number based on a specified mean (as a percent of lane_berfore)
    if percent >= 1:
        print("Error: percent must in between 0 and 1")
    else:
        possible_values = np.arange(0, lane_before + 1)
        target_mean = percent * lane_before

        # Heuristic adjustment: Generate a probability distribution that attempts
        # to reflect the target mean by adjusting the weight inversely with the distance
        # to the target mean. This is a simplified approach and might need fine-tuning
        # for specific requirements.
        mean_adjustment_factor = np.abs(possible_values - target_mean)
        probabilities = 1 / (1 + mean_adjustment_factor)
        probabilities = probabilities / probabilities.sum()  # Normalize to sum to 1
        return np.random.choice(possible_values, size=size, p=probabilities)[0]


def sample_closedlanenum(Stage_string, FS_rlz_scalar, lane_before,
                         closed_lane_IFS_rlz_scalar = None):
    ## Sample closed lane number during the two phases
    #- input
    # Stage_string = 'Initial' or 'Reopening', to indicate whether it is for an Initial FS or reopneing FS.
    # FS_list_rlz: a list of system Initial FS per rlz
    # lane_before: scalar, # of closed lanes before an earthquake
    # closed_lane_IFS_rlz_scalar: needed in reopening phase, how many lanes closed during the initial response phase
    #- output
    #  a scalar of closed lane number
    #  (for reopening phase only), a tag indicating whether weight restriction is triggered
    random.seed(1223)
    np.random.seed(1223)

    if FS_rlz_scalar not in range(0,8):
        raise ValueError("FS_rlz_scalar must be in between [0,7]")
    else:
        if Stage_string.lower() == 'Initial'.lower():
            if FS_rlz_scalar in [0,1]: # no lane closed
                return 0
            elif FS_rlz_scalar == 7: # all lane closed
                return lane_before
            elif FS_rlz_scalar == 2: # Moderate Lane Closure
                #----- begin sampling for FS == 2
                if lane_before <=3:
                    return 1
                elif lane_before == 4: #FS == 2, lane_before==4, 75% close 1 lane; 25% close 2 lane
                    return  random.choices([1,2], weights = [.75,.25], k=1)[0]
                elif lane_before == 5: #FS == 2, lane_before==5, 62.5% close 1 lane; 25% close 2 lanes; 12.5% close 3 lanes
                    return  random.choices([1,2,3], weights = [.625,.25,.125], k=1)[0]
                elif lane_before == 6: #FS == 2, lane_before==6, 67.5% close 1 lane; 12.5% close 2 lanes; 12.5% close 3 lanes, 7.5% close 4 lanes
                    return  random.choices([1,2,3,4], weights = [.675,.125,.125,.075], k=1)[0]
                else: #FS == 2, lane_before>6, on avg 25% of tot lanes closed
                    percent_IFS3 = .25
                    return rd_num_byMean(percent_IFS3, lane_before)

            elif FS_rlz_scalar == 3: #  Extensive Lane Closure
                #----- begin sampling for FS == 3
                if lane_before <=2:
                    return 1
                elif lane_before == 3: #FS == 3, lane_before==3, 25% close 1 lane; 75% close 
                    #return  random.choices([1,2], weights = [.25, .75], k=1)[0]
                    return 2
                elif lane_before == 4: #FS == 3, lane_before==4, 25% close 1 lane; 75% close 2 lanse; 25% close 3 lanes
                    #return  random.choices([1,2,3], weights = [.25,.75,.25], k=1)[0]
                    return 3
                elif lane_before == 5: #FS == 3, lane_before==5
                    #return  random.choices([2,3,4], weights = [.125,.5,.375], k=1)[0]
                    return  random.choices([3,4], weights = [.25, .75], k=1)[0]
                elif lane_before == 6: #FS == 3
                    #return  random.choices([3,4,5], weights = [.125,.5,.375], k=1)[0]
                    return  random.choices([4,5], weights = [.5,.5], k=1)[0]
                else: #IFS == 3, lane_before>6, on avg 25% of tot lanes closed
                    percent_IFS4 = .75
                    return rd_num_byMean(percent_IFS4, lane_before)


        elif Stage_string.lower() == 'Reopening'.lower():
            # To determine the closed lane # in Reopneing State, the sampled lane value from its corresponding Initial FS is required
            if closed_lane_IFS_rlz_scalar is None:
                raise ValueError("The arg 'closed_lane_IFS_rlz_scalar' is required when sampling closed lane # in reopnein state")
            else:
                weight_restriction_tag = 0
                
                if FS_rlz_scalar in [0,1]: # no lane closed
                    return (0,weight_restriction_tag)
                
                elif FS_rlz_scalar == 4: # weight restriction only
                    weight_restriction_tag = 1
                    return (0, 1)
                
                elif FS_rlz_scalar == 7: # FS7: Complete Closure
                    return (lane_before,weight_restriction_tag)
                
                elif FS_rlz_scalar in [2,3]: # Maintain the previous decision
                    return (closed_lane_IFS_rlz_scalar,weight_restriction_tag)
                
                elif FS_rlz_scalar in [5,6]: # Minor lane restriction 
                    if lane_before <=4:
                        closedlane_Reop = 1
                    elif lane_before == 5: 
                        closedlane_Reop = random.choices([1,2], weights = [.875,.125], k=1)[0]
                        while (closedlane_Reop > closed_lane_IFS_rlz_scalar) or (closedlane_Reop < 1): # Ensure the closed lane under FS 5 or 6 must be smaler than that in initial phase, but still >=1
                            closedlane_Reop = random.choices([1,2], weights = [.875,.125], k=1)[0]
                    elif lane_before == 6: 
                        closedlane_Reop = random.choices([1,2,3], weights = [.675,.125,.125], k=1)[0]
                        while (closedlane_Reop > closed_lane_IFS_rlz_scalar) or (closedlane_Reop < 1): # Ensure the closed lane under FS 5 or 6 must be smaler than that in initial phase, but still >=1
                            closedlane_Reop = random.choices([1,2,3], weights = [.675,.125,.125], k=1)[0]

                    else: # lane number before > 6
                        percent_Reopn = .2 
                        closedlane_Reop = lane_before
                        while (closedlane_Reop > closed_lane_IFS_rlz_scalar) or (closedlane_Reop < 1): # Ensure the closed lane under FS 5 or 6 must be smaler than that in initial phase, but still >=1
                            closedlane_Reop = rd_num_byMean(percent_Reopn, lane_before)

                    if FS_rlz_scalar == 6: # combined with weight restriction
                        weight_restriction_tag = 1
                        
                    return (closedlane_Reop,weight_restriction_tag)
                else:
                    raise ValueError("There's some event not considered in this function") 
                    
        else:
            raise ValueError("Error: Invalid input of 'Stage_string'. Please provide 'Initial' or 'Reopening'.")
            