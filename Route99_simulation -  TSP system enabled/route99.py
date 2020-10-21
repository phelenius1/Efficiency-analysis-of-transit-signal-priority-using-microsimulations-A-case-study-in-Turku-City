import os
import sys
import optparse

# we need to import some python modules from the $SUMO_HOME/tools directory
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

from sumolib import checkBinary  # Checks for the binary in environ vars
import traci


def get_options():
    opt_parser = optparse.OptionParser()
    opt_parser.add_option("--nogui", action="store_true",
                         default=False, help="run the commandline version of sumo")
    options, args = opt_parser.parse_args()
    return options
def get_phase(TrafficNumber):
    x = int(traci.trafficlight.getPhase(TrafficNumber))
    return x

#Global variables
ExtensionGiven = {}
LastExtension = {}
Extensions = 0
RedShortenings = 0
TotalExtraGreen = 0
RedShortTrafficLight = 0   #This one shows when there's been a red shortening for a bus, but unlike RedShortenings, it doesn't count every phase.
#HÄr e någo fittit weird
def TrafficLightExtension(x, max):
    global Extensions
    global ExtensionGiven
    global LastExtension
    if traci.trafficlight.getNextSwitch(x)- traci.simulation.getTime() == 0:            #Check time remaining if 1 second then give extension
        traci.trafficlight.setPhaseDuration(x,max)
        ExtensionGiven[x] = 1
        Extensions += 1

        

def RedShorter(TrafficNumber, MinTime):
    global RedShortenings
    phaseDurationLeft = int(traci.trafficlight.getNextSwitch(TrafficNumber)- traci.simulation.getTime())    #How much time is left of current phase
    phaseTotalDuration = int(traci.trafficlight.getPhaseDuration(TrafficNumber))                            #Total phase duration
    MinMax = min(max(MinTime-(phaseTotalDuration-phaseDurationLeft),0), MinTime)                            #Calculates if the light should be shorted and by how much.
    traci.trafficlight.setPhaseDuration(TrafficNumber,MinMax)




# contains TraCI control loop
#This is where the simulation runs
def run():

    global ExtensionGiven 
    global LastExtension 
    global Extensions 
    global RedShortenings 
    global TotalExtraGreen
    global RedShortTrafficLight



    #Set simulation variables to 0
    step = 0
    x = 0
    RedShort = 0
    #This is to check if the current red light has already been shortened
    Redshortened = {"333": {3:0,
                            6:0 
                    },
                    "334":{3:0,
                           6:0
                    },
                    "336":{0:0,
                    },
                    "338":{3:0,
                           6:0
                    },
                    "405":{0:0,
                           3:0,
                           9:0
                    },
                    "409":{0:0,
                           3:0,
                           9:0
                    },
                    "410":{3:0,
                           6:0
                    },
                    "420":{3:0
                    }
    }
    #Gives the minimum phase time. The first key is the intersection number. The second key
    #in the nested dictionary is the phase number that can be shortened and the value tells us
    #what the minimum time for that phase is.
    #The extension key, tells which phase can be extended and by how much it can be extended. The phase
    #that can be extended is always in the first position(index 0) in the list and the extension time is
    #in the second position (index 1)
    MinimumPhaseTime = {    "333": {3:6,
                                    6:6,
                                    "extension":[0,30]
                            },
                            "334": {6:15,
                                    3:7,
                                    "extension":[0,30]
                            },
                            "336": {0:0,
                                    "extension":[3,20]
                            },
                            "338": {3:0,
                                    6:0,
                                    "extension":[0,30]
                            },
                            "405": {0:15,
                                    3:6,
                                    9:8,
                                    "extension":[6,30]
                            },
                            "409": {0:12,
                                    3:8,
                                    9:10,
                                    "extension":[6,25]
                            },
                            "420": {3:12,
                                    "extension":[0,30]
                            }
    }
                          #To check if the sixth phase has been shortened
    vehicleIDsBefore = {}       #This stores all the before the intersection detector values from the current step in the simulation
    vehicleIDsAfter = {}        #This stores all the after the intersection detector values from the current step in the simulation
    BusPriorityRequested = {}           #To check if there is buses in the intersection currently

    ExtraGreen ={"334":[0,2,14, 6] #[(0= no extra green, 1 = extra green ongoing; 2 extra green allowed to end, 3=extra green shortened),phase when it should continue normaly
                ,"409":[0,8,10,0]  # minimum time of extra green, phase that continues]
    }


    ExtraGreenRequest = {"334": [5,0]            #[phase where extra green is applied, green phase]
                        ,"409": [11,6]
    }


    All_intersections = ["333", "334", "336", "338", "405", "409", "410", "420"]
    
    #Create the variables
    for x in All_intersections:
        BusPriorityRequested[x] = []
        ExtensionGiven[x] = 0

    #Intersection 334

    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        step += 1

#Retrieve loop data. Sometimes there are detectors for longer distances that needs to be added here. 
#60m: Remove: 334E_B3; add: 420W_B2,420E_B2, 334_B3
#90m:  Remove: Add 420E_B2; Remove: 334E_B3
#120m: Remove: 334E_B3,420E_B2, 334E_B3
#In 150m: Remove:  409W_B2, 420E_B2,420W_B2; add: 334E_B3
#180m: 409W_B2, 420E_B2,420W_B2; add: 334E_B3
        vehicleIDsBefore["333"] = traci.inductionloop.getLastStepVehicleIDs("333E_B1") + traci.inductionloop.getLastStepVehicleIDs("333E_B2") + traci.inductionloop.getLastStepVehicleIDs("333E_B3") + traci.inductionloop.getLastStepVehicleIDs("333W_B1") + traci.inductionloop.getLastStepVehicleIDs("333W_B2")
        vehicleIDsAfter["333"] = traci.inductionloop.getLastStepVehicleIDs("333E_A1") + traci.inductionloop.getLastStepVehicleIDs("333E_A2") + traci.inductionloop.getLastStepVehicleIDs("333W_A1") + traci.inductionloop.getLastStepVehicleIDs("333W_A2")

        vehicleIDsBefore["334"] = traci.inductionloop.getLastStepVehicleIDs("334E_B1") + traci.inductionloop.getLastStepVehicleIDs("334E_B2") + traci.inductionloop.getLastStepVehicleIDs("334E_B3") + traci.inductionloop.getLastStepVehicleIDs("334W_B1") + traci.inductionloop.getLastStepVehicleIDs("334W_B2")
        vehicleIDsAfter["334"] = traci.inductionloop.getLastStepVehicleIDs("334E_A1") + traci.inductionloop.getLastStepVehicleIDs("334E_A2") + traci.inductionloop.getLastStepVehicleIDs("334W_A1") + traci.inductionloop.getLastStepVehicleIDs("334W_A2")

        vehicleIDsBefore["336"] = traci.inductionloop.getLastStepVehicleIDs("336E_B1") + traci.inductionloop.getLastStepVehicleIDs("336W_B1") 
        vehicleIDsAfter["336"] = traci.inductionloop.getLastStepVehicleIDs("336E_A1") + traci.inductionloop.getLastStepVehicleIDs("336W_A1")

        vehicleIDsBefore["338"] = traci.inductionloop.getLastStepVehicleIDs("338E_B1") + traci.inductionloop.getLastStepVehicleIDs("338W_B1") 
        vehicleIDsAfter["338"] = traci.inductionloop.getLastStepVehicleIDs("338E_A1") + traci.inductionloop.getLastStepVehicleIDs("338W_A1")

        vehicleIDsBefore["405"] = traci.inductionloop.getLastStepVehicleIDs("405E_B1") + traci.inductionloop.getLastStepVehicleIDs("405W_B1") + traci.inductionloop.getLastStepVehicleIDs("405E_B2")
        vehicleIDsAfter["405"] = traci.inductionloop.getLastStepVehicleIDs("405E_A1") + traci.inductionloop.getLastStepVehicleIDs("405W_A1")

        vehicleIDsBefore["409"] = traci.inductionloop.getLastStepVehicleIDs("409E_B1") + traci.inductionloop.getLastStepVehicleIDs("409W_B1")# + traci.inductionloop.getLastStepVehicleIDs("409W_B2")
        vehicleIDsAfter["409"] = traci.inductionloop.getLastStepVehicleIDs("409E_A1") + traci.inductionloop.getLastStepVehicleIDs("409E_A2") + traci.inductionloop.getLastStepVehicleIDs("409W_A1") + traci.inductionloop.getLastStepVehicleIDs("409W_A2")

        vehicleIDsBefore["410"] = traci.inductionloop.getLastStepVehicleIDs("410E_B1") + traci.inductionloop.getLastStepVehicleIDs("410W_B1")
        vehicleIDsAfter["410"] = traci.inductionloop.getLastStepVehicleIDs("410E_A1") +  traci.inductionloop.getLastStepVehicleIDs("410W_A1")

        vehicleIDsBefore["420"] = traci.inductionloop.getLastStepVehicleIDs("420E_B1") + traci.inductionloop.getLastStepVehicleIDs("420W_B1")#+ traci.inductionloop.getLastStepVehicleIDs("420W_B2") + traci.inductionloop.getLastStepVehicleIDs("420E_B2") 
        vehicleIDsAfter["420"] = traci.inductionloop.getLastStepVehicleIDs("420E_A1") + traci.inductionloop.getLastStepVehicleIDs("420W_A1")

        #Check if any buses drove past a detector
        for intersection in vehicleIDsBefore:
            if "bus" in str(vehicleIDsBefore[intersection]):
                for vehicle in vehicleIDsBefore[intersection]:
                    if 'bus' in vehicle:
                        if vehicle not in BusPriorityRequested[intersection]:
                            BusPriorityRequested[intersection].append(vehicle)
                            
        
        #Extra green
        for intersection in ExtraGreenRequest:
            if ExtraGreen[intersection][0] != 0:
                continue
            elif len(BusPriorityRequested[intersection]) != 0:
                if ExtraGreenRequest[intersection][0] == get_phase(intersection):                           #Check if the current phase is the phase before the extra green can be implemented
                    if int(traci.trafficlight.getNextSwitch(intersection) - traci.simulation.getTime()) == 0:       #Switches to green phase
                        traci.trafficlight.setPhase(intersection, ExtraGreenRequest[intersection][1])
                        ExtraGreen[intersection][0] = 1
                        TotalExtraGreen += 1
            
        #First Checks if there are any busses in the intersections
        #Checks if the current phase can be shorten and shortens it
        #The index(get_Phase) of the traffic phases can be seen in netedit or directly in the net-file.
        for intersection in MinimumPhaseTime:
            if len(BusPriorityRequested[intersection]) != 0:                                                #Checks if there is any buses in the intersection
                for phase in MinimumPhaseTime[intersection]:
                    if phase == get_phase(intersection) and Redshortened[intersection][phase] == 0 and intersection != "410":         #Checks if the current phase can be shortened and if it has already been shortened
                        RedShorter(intersection, MinimumPhaseTime[intersection][phase])
                        Redshortened[intersection][phase] = 1
                    elif phase == "extension" and ExtensionGiven[intersection] != 1 and intersection != "410": #Check if current intersection is allowed to have extension, check if there is an extension on going and check if it is an extra green.
                        if MinimumPhaseTime[intersection][phase][0] == get_phase(intersection):
                            TrafficLightExtension(intersection, MinimumPhaseTime[intersection][phase][1])
                         
                          



        #Intersection 410, special case because the extension depends on what direction the bus is going
        #Did not do for 338 because extending phase 3 would go over the maximum time for turning direction
        if len(BusPriorityRequested["410"]) != 0:
            phase = get_phase("410")
            #Only for busses going east
            if "bus_W" not in str(BusPriorityRequested["410"]):             #Only for busses going east
                #Shorten current phase
                if phase == 6 and Redshortened["410"][6] == 0:
                    RedShorter("410", 6)
                    Redshortened["410"][6] = 1
                #Extension
                elif phase == 0 and ExtensionGiven["410"] == 0:
                    TrafficLightExtension("410", 30)
                elif phase == 3 and ExtensionGiven["410"] == 0:
                    TrafficLightExtension("410", 30)
            else:
                #Shorten current phase, even if there is an extension for phase 3, while a bus is incoming from west, 
                #it's not a problem because phase 3 will then be shortened. Happens when bus from both directions
                if phase == 3 and Redshortened["410"][3] == 0:
                    RedShorter("410", 20)
                    Redshortened["410"][3] = 1
                elif phase == 6 and Redshortened["410"][6] == 0:
                    RedShorter("410", 6)
                    Redshortened["410"][6] = 1
                #Extension
                elif  phase == 0 and ExtensionGiven["410"] == 0:
                    TrafficLightExtension("410", 30)
                    

        for intersection in vehicleIDsAfter:
            if "bus" in str(vehicleIDsAfter[intersection]):
                for x in vehicleIDsAfter[intersection]:
                    try:
                        BusPriorityRequested[intersection].remove(x) #Removes bus from priority list, must be try because the bus sometimes triggers the detectors twice
                    except:
                        pass
                    if BusPriorityRequested[intersection] == []:        #Checks that no other buses are in the same intersection at the moment.
                        if intersection in ExtensionGiven:
                            if ExtensionGiven[intersection] == 1:
                                ExtensionGiven[intersection] = 0
                                traci.trafficlight.setPhaseDuration(intersection,0)
                        for TrafficPhase in Redshortened[intersection]:
                            if Redshortened[intersection][TrafficPhase] == 1:
                                Redshortened[intersection][TrafficPhase] = 0
                                RedShortenings += 1
                                RedShort = 1
                        if RedShort == 1:
                            RedShortTrafficLight +=1
                            RedShort = 0
                        if intersection in ExtraGreen:
                            if ExtraGreen[intersection][0] == 1:
                                ExtraGreen[intersection][0] = 2
                               
                    
        #This ends the extra green and keeps track of phases
        for intersection in ExtraGreen:
            #Shorten the phase if possible
            if ExtraGreen[intersection][0] == 2:
                RedShorter(intersection, ExtraGreen[intersection][2])
                ExtraGreen[intersection][0] = 3
            #Continue the cycle as it was before the extra green
            if ExtraGreen[intersection][0] == 3:
                if get_phase(intersection) == ExtraGreen[intersection][1]:
                    if int(traci.trafficlight.getNextSwitch(intersection) - traci.simulation.getTime()) == 0:
                        traci.trafficlight.setPhase(intersection, ExtraGreen[intersection][3])
                        ExtraGreen[intersection][0] = 0
                        
    traci.close()
    sys.stdout.flush()
    print("Extra Greens: ",TotalExtraGreen, "\nRedShortenings: ", RedShortenings, "\nRedShortInTrafficLight: ", RedShortTrafficLight, "\nExtensions: ",Extensions)

# main entry point
if __name__ == "__main__":
    options = get_options()

    # check binary
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    # traci starts sumo as a subprocess and then this script connects and runs
    traci.start([sumoBinary, "-c", "route99.sumocfg",
                             "--tripinfo-output", "tripinfo99_Priority.xml",
                              ])
    run()