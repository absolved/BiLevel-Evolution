First, download and install all packages listed in requirements.txt

Use "python sept24_bilevel_evolution.py" to run with the set parameter values.
Results of each trial will be saved to a file 'evolutionary_results.txt', which will be appended to on subsequent runs.

The following parameters can be changed within sept24_bilevel_evolution to guide the evolution:

        POP_SIZE = 100 #number of offspring per generation
        num_gen = 40 #number of reproductive events
        mutpb = .5 #mutation probability on the population level
        indpb = .25 #mutation probability on the individual level for each attack location
        cxpb = .5 #crossover probability

Within the python code some paths may have to be changed to match paths on the machine being used.        