# Efficiency analysis of transit signal priority using microsimulations: A case study in Turku City

##To run the simulation you have to install the following programs and configure the following variables. 
1.	Download SUMO (https://sumo.dlr.de/docs/Downloads.php)
2.	Download Python (https://www.python.org/	
3.	Add SUMO_HOME to system variables for more information https://sumo.dlr.de/docs/Basics/Basic_Computer_Skills.html

##Start simulation
1.	Once the setups are done the simulations can be ran by clicking the run.bat file. 
2.	The output files with the original settings are summary output and tripinfo. However, more outputs can be added to the route99.sumocfg files. For more information about SUMO outputs visit https://sumo.dlr.de/docs/Simulation/Output.html

##Choosing the correct seeds
1.	If the results are to be replicated, then identical seeds must be used. In the sumocfg file there is a row called random number and seed value. In the seed value row, there are five seed values commented. These five values should be used to copy the results. In the simulation the vehicle spawn is randomised and therefore it is crucial to have the same seed values. 

##Changing the detector distance 
1.	There are two ways to change the detector distance values. The most efficient way is to open Route99.sumocfg and change the busdetectors.add.xml to for example “busdetector_60m.add.xml”. The other way is to copy the contents from one of the busdetector files with meters in their name and paste it to the original busdetectors.add.file.
2.	In some distances the number of lanes change when moving the detectors. Therefore, the number of detectors must be updated in the route.py file. The retrieval of detector data can be found on rows 161-190. The comments above the retrieval code describes which detectors should be included for each detector distance. 
