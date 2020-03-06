# Params.py

This is just a library which reads the Settings.json file and populates a dictionary (Params).

It also defines the names of the parameters as PARAM_xxxxx to avoid conflicts and clearly identify them in the code.

In addition it defines default values for the parameters.

## readParams(fname)  
fname: string name of json data file to read  
Reads the specified file , json decodes it and populates the Params dictionary

## saveParams(fname) 
fname: target json file to (over)write  
Json encodes the Params dictionary and writes it to the specified file. If the file exists it is over-written.
