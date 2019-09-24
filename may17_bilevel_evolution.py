import random, array, os, sys
import gams
import createGAMS_XML
from deap import base, creator, tools, gp, algorithms
import base64
import neosclient
import numpy
import datetime
  
#GAMS Model which is being solved at lower level  
def get_model_text():
    return '''
Set i nodes
    Alias (i,destination,destination2);
Set realNodes(i)
    Alias (realNodes,realDest);
Sets
    k commodities
    VirtualSource(i) 
    VirtualDest(i) 
    edgelist(i,destination);
Parameters
    c(i) cost of attacking node i
    u(i,destination,k) upper bound on flow of commodity k through arc j
    b(i,k) demand of node i for commodity k
    s(i,k) supply of node i for commodity k;
Scalar M attackers budget /1/
       lambda target efficiency /.7/
       totsup total supply /20/;
$GDXIN in.gdx       
$load i k realNodes VirtualSource VirtualDest edgelist u b s
$GDXIN in.gdx
Variables
       objout
       x(i,destination) edge disabled or enabled
       f(i,destination,k) flow of commodity k across arc j
       z(i,destination,k) dummy variable to prevent looped phantom flows
       y(k) total flow of commodity k through the system;

Binary variables x, z;
positive variable f,y;

Equations
       defout
       e1(i,destination,k)   failure cascade constraint
       e2(i,destination,k)   flow capacity constraint
       e3(realNodes,k)
       e4(VirtualSource,k) s constraint
       e5(VirtualDest,k) t constraint
       e6(i,destination,k)   directional flow constraint
       e7(i,destination,k)   directional flow constraint;

       defout .. objout =e= Sum(k,y(k));
       
       e1(i,destination,k) $ (b(i,k) <> 0) .. x(i,destination)*b(i,k) =l= Sum(destination2,f(destination2,i,k) $ edgelist(destination2,i));
       
       e2(i,destination,k) $ edgelist(i,destination) .. f(i,destination,k) =l= x(i,destination)*u(i,destination,k);
       
       e3(realNodes,k) .. Sum(i,f(i,realNodes,k) $ edgelist(i,realNodes)) - Sum(i,f(realNodes,i,k) $ edgelist(realNodes,i)) =e= 0;  
       
       e4(VirtualSource,k) .. Sum(realNodes,f(VirtualSource,realNodes,k) $ edgelist(VirtualSource,realNodes))- Sum(realNodes,f(realNodes,VirtualSource,k) $ edgelist(realNodes,VirtualSource)) =e= y(k);
       
       e5(VirtualDest,k) .. Sum(realNodes,f(VirtualDest,realNodes,k) $ edgelist(VirtualDest,realNodes))- Sum(realNodes,f(realNodes,VirtualDest,k) $ edgelist(realNodes,VirtualDest)) =e= -y(k);

       e6(i,destination,k) $ edgelist(i,destination) .. f(i,destination,k) =l= 1000*z(i,destination,k);

       e7(i,destination,k) $ edgelist(i,destination) .. z(i,destination,k) + z(destination,i,k) =e= 1;

Model multinetwork /all/;

solve multinetwork using mip max objout;'''

#solves the lower level max flow problem for the specific attack
def solveGAMS(attacked):
    #if (len(sys.argv) > 1):
    #   ws = gams.GamsWorkspace(system_directory = sys.argv[1]) 
    #else:
    #    ws = gams.GamsWorkspace(debug = 0)
    ws = gams.GamsWorkspace(debug = 0)
    nodes = ["s","A","a2","a3","a4","B","b1","b2","b3","b4","C","c1","c2","c3","c4","t"]
    edges = [("A","a2"),
("A","a3" ),
("A","a4"),
("a2","B"),
("a2","b1"),
("a2","b2"),
("a2","b3"),
("a2","b4"),
("a3","A"),
("a3","C"),
("B","b1"),
("B","b2"),
("B","b3"),
("B","b4"),
("b3","C"),
("b4","A"),
("b4","a2"),
("b4","a3"),
("b4","a4"),
("C","c1"),
("C","c2"),
("C","c3"),
("C","c4"),
("c1","B"),
("c1","b1"),
("c1","b2"),
("c1","b3"),
("c1","b4"),
("c2","c1"),
("c2","c3"),
("c3","c2"),
("c3","c4"),
("c4","A"),
("c4","a2"),
("c4","a3"),
("c4","a4"),
("s","A"),
("s","B"),
("s","C"),
("A","t"),
("a2","t"),
("a3","t"),
("a4","t"),
("B","t"),
("b1","t"),
("b2","t"),
("b3","t"),
("b4","t"),
("C","t"),
("c1","t"),
("c2","t"),
("c3","t"),
("c4","t")]

    capacity={("A","a2", "water"):4,("A","a2", "power"):4,("A","a2", "cyber"):4,
("A","a3", "water"):4,("A","a3", "power"):4,("A","a3", "cyber"):4,
("A","a4", "water"):4,("A","a4", "power"):4,("A","a4", "cyber"):4,
("a2","B", "water"):2,("a2","B", "power"):0,("a2","B", "cyber"):0,
("a2","b1", "water"):2,("a2","b1", "power"):0,("a2","b1", "cyber"):0,
("a2","b2", "water"):2,("a2","b2", "power"):0,("a2","b2", "cyber"):0,
("a2","b3", "water"):2,("a2","b3", "power"):0,("a2","b3", "cyber"):0,
("a2","b4", "water"):2,("a2","b4", "power"):0,("a2","b4", "cyber"):0,
("a3","A", "water"):4,("a3","A", "power"):4,("a3","A", "cyber"):4,
("a3","C", "water"):2,("a3","C", "power"):0,("a3","C", "cyber"):0,
("B","b1", "water"):4,("B","b1", "power"):4,("B","b1", "cyber"):4,
("B","b2", "water"):4,("B","b2", "power"):4,("B","b2", "cyber"):4,
("B","b3", "water"):4,("B","b3", "power"):4,("B","b3", "cyber"):4,
("B","b4", "water"):4,("B","b4", "power"):4,("B","b4", "cyber"):4,
("b3","C", "water"):0,("b3","C", "power"):0,("b3","C", "cyber"):4,
("b4","A", "water"):0,("b4","A", "power"):0,("b4","A", "cyber"):4,
("b4","a2", "water"):0,("b4","a2", "power"):0,("b4","a2", "cyber"):4,
("b4","a3", "water"):0,("b4","a3", "power"):0,("b4","a3", "cyber"):4,
("b4","a4", "water"):0,("b4","a4", "power"):0,("b4","a4", "cyber"):4,
("C","c1", "water"):4,("C","c1", "power"):4,("C","c1", "cyber"):4,
("C","c2", "water"):4,("C","c2", "power"):4,("C","c2", "cyber"):4,
("C","c3", "water"):4,("C","c3", "power"):4,("C","c3", "cyber"):4,
("C","c4", "water"):4,("C","c4", "power"):4,("C","c4", "cyber"):4,
("c1","B", "water"):2,("c1","B", "power"):0,("c1","B", "cyber"):0,
("c1","b1", "water"):2,("c1","b1", "power"):0,("c1","b1", "cyber"):0,
("c1","b2", "water"):2,("c1","b2", "power"):0,("c1","b2", "cyber"):0,
("c1","b3", "water"):2,("c1","b3", "power"):0,("c1","b3", "cyber"):0,
("c1","b4", "water"):2,("c1","b4", "power"):0,("c1","b4", "cyber"):0,
("c2","c1", "water"):4,("c2","c1", "power"):4,("c2","c1", "cyber"):4,
("c2","c3", "water"):4,("c2","c3", "power"):4,("c2","c3", "cyber"):4,
("c3","c2", "water"):4,("c3","c2", "power"):4,("c3","c2", "cyber"):4,
("c3","c4", "water"):4,("c3","c4", "power"):4,("c3","c4", "cyber"):4,
("c4","A", "water"):2,("c4","A", "power"):2,("c4","A", "cyber"):2,
("c4","a2", "water"):2,("c4","a2", "power"):2,("c4","a2", "cyber"):2,
("c4","a3", "water"):2,("c4","a3", "power"):2,("c4","a3", "cyber"):2,
("c4","a4", "water"):2,("c4","a4", "power"):2,("c4","a4", "cyber"):2,
("s","A", "water"):4,("s","A", "power"):1,("s","A", "cyber"):1,
("s","B", "water"):2,("s","B", "power"):1,("s","B", "cyber"):4,
("s","C", "water"):1,("s","C", "power"):4,("s","C", "cyber"):2,
("A","t", "water"):0,("A","t", "power"):1,("A","t", "cyber"):1,
("a2","t", "water"):1,("a2","t", "power"):1,("a2","t", "cyber"):1,
("a3","t", "water"):1,("a3","t", "power"):1,("a3","t", "cyber"):1,
("a4","t", "water"):1,("a4","t", "power"):1,("a4","t", "cyber"):1,
("B","t", "water"):1,("B","t", "power"):1,("B","t", "cyber"):0,
("b1","t", "water"):1,("b1","t", "power"):1,("b1","t", "cyber"):1,
("b2","t", "water"):1,("b2","t", "power"):1,("b2","t", "cyber"):1,
("b3","t", "water"):1,("b3","t", "power"):1,("b3","t", "cyber"):1,
("b4","t", "water"):1,("b4","t", "power"):1,("b4","t", "cyber"):1,
("C","t", "water"):1,("C","t", "power"):0,("C","t", "cyber"):1,
("c1","t", "water"):1,("c1","t", "power"):1,("c1","t", "cyber"):1,
("c2","t", "water"):1,("c2","t", "power"):1,("c2","t", "cyber"):1,
("c3","t", "water"):1,("c3","t", "power"):1,("c3","t", "cyber"):1,
("c4","t", "water"):1,("c4","t", "power"):1,("c4","t", "cyber"):1}

#    demand ={"A":(0,1,1),
#"a2":(1,1,1),
#"a3":(1,1,1),
#"a4":(1,1,1),
#"B":(1,1,0),
#"b1":(1,1,1),
#"b2":(1,1,1),
#"b3":(1,1,1),
#"b4":(1,1,1),
#"C"	:(1,0,1),
#"c1":(1,1,1),
#"c2":(1,1,1),
#"c3":(1,1,1),
#"c4":(1,1,1),
#"s":(0,0,0),
#"t":(0,0,0)}
    demand={("A","water"):0,("A","power"):1,("A","cyber"):1,("a2","water"):1,("a2","power"):1,("a2","cyber"):1,("a3","water"):1,("a3","power"):1,("a3","cyber"):1,("a4","water"):1,("a4","power"):1,("a4","cyber"):1,("B","water"):1,("B","power"):1,("B","cyber"):0,("b1","water"):1,("b1","power"):1,("b1","cyber"):1,("b2","water"):1,("b2","power"):1,("b2","cyber"):1,("b3","water"):1,("b3","power"):1,("b3","cyber"):1,("b4","water"):1,("b4","power"):1,("b4","cyber"):1,("C","water"):1,("C","power"):0,("C","cyber"):1,("c1","water"):1,("c1","power"):1,("c1","cyber"):1,("c2","water"):1,("c2","power"):1,("c2","cyber"):1,("c3","water"):1,("c3","power"):1,("c3","cyber"):1,("c4","water"):1,("c4","power"):1,("c4","cyber"):1,("s","water"):0,("s","power"):0,("s","cyber"):0,("t","water"):0,("t","power"):0,("t","cyber"):0}

    supply={("A","water"):4,("A","power"):1,("A","cyber"):1,("a2","water"):0,("a2","power"):0,("a2","cyber"):0,("a3","water"):0,("a3","power"):0,("a3","cyber"):0,("a4","water"):0,("a4","power"):0,("a4","cyber"):0,("B","water"):2,("B","power"):1,("B","cyber"):4,("b1","water"):0,("b1","power"):0,("b1","cyber"):0,("b2","water"):0,("b2","power"):0,("b2","cyber"):0,("b3","water"):0,("b3","power"):0,("b3","cyber"):0,("b4","water"):0,("b4","power"):0,("b4","cyber"):0,("C","water"):1,("C","power"):4,("C","cyber"):2,("c1","water"):0,("c1","power"):0,("c1","cyber"):0,("c2","water"):0,("c2","power"):0,("c2","cyber"):0,("c3","water"):0,("c3","power"):0,("c3","cyber"):0,("c4","water"):0,("c4","power"):0,("c4","cyber"):0,("s","water"):0,("s","power"):0,("s","cyber"):0,("t","water"):0,("t","power"):0,("t","cyber"):0}
#    supply={"A"	:(4,1,1),
#"a2":(0,0,0),
#"a3":(0,0,0),
#"a4":(0,0,0),
#"B":(2,1,4),
#"b1":(0,0,0),
#"b2":(0,0,0),
#"b3":(0,0,0),
#"b4":(0,0,0),
#"C":(1,4,2),
#"c1":(0,0,0),
#"c2":(0,0,0),
#"c3":(0,0,0),
#"c4":(0,0,0),
#"s":(0,0,0),
#"t":(0,0,0)}

    commlist = ["water","power","cyber"]

    attackedNodes = []

    db = ws.add_database()
    i = db.add_set("i", 1, "nodes")

    k = db.add_set("k", 1, "commodities")
    for comm in commlist:
        k.add_record(comm)

    realNodes = db.add_set("realNodes", 1, "realNodes")
    VirtualSource = db.add_set("VirtualSource", 1, "VirtualSource")
    VirtualDest = db.add_set("VirtualDest", 1, "VirtualDest")
    edgelist = db.add_set("edgelist", 2, "edges")

    #u = gams.GamsParameter(db, "u", 3, "upper bound on flow across arc (i,j)")
    #b = gams.GamsParameter(db, "b", 1, "demand vector for node i")
    #s = gams.GamsParameter(db, "s", 3, "supply vector for node i")

    #u = db.add_parameter_dc("u", [edges,k], "upper bound on flow across arc (i,j)")
    b = db.add_parameter_dc("b", [i,k], "demand of node i for commodity k")
    s = db.add_parameter_dc("s", [i,k], "supply of node i for commodity k")
    u = db.add_parameter_dc("u", [i,i,k], "capacity of edge for commodity k")
    #for edge in edgelist:
    #    u.add_record(edge).value = capacity(edge)
    #only add nodes to graph which have not been attacked (x_i = 0)
    for j in range(0,len(nodes)):
        if attacked[j] == 0:
            i.add_record(nodes[j])
            
            for comm in commlist:
                b.add_record((nodes[j],comm)).value = demand[(nodes[j],comm)]
                s.add_record((nodes[j],comm)).value = supply[(nodes[j],comm)]
            if (nodes[j] == "s"):
                VirtualSource.add_record(nodes[j])
            elif (nodes[j] == "t"):
                VirtualDest.add_record(nodes[j])
            else:
                realNodes.add_record(nodes[j])        

        else:
            attackedNodes.append(nodes[j]) 

    #only add edges which arent connected to attacked nodes           
    for j in range(0,len(edges)):
        if edges[j][0] in attackedNodes or edges[j][1] in attackedNodes:
            continue
        else:
            edgelist.add_record(edges[j])
            u.add_record((edges[j][0],edges[j][1], "water")).value = capacity[(edges[j][0],edges[j][1], "water")]
            u.add_record((edges[j][0],edges[j][1], "power")).value = capacity[(edges[j][0],edges[j][1], "power")]
            u.add_record((edges[j][0],edges[j][1], "cyber")).value = capacity[(edges[j][0],edges[j][1], "cyber")]

    #model = ws.add_job_from_string(get_model_text())
    #opt = ws.add_options()
    #opt.defines["gdxincname"] = db.name
    #opt.all_model_types = "xpress"
    #model.run(opt, databases = db)

    #data = ws.add_job_from_string(get_data_text())
    #data.run()
    #job = gams.GamsJob(ws, source = get_model_text())
    #dont know what this stuff does
    #opt = ws.add_options()
    #opt.defines["gdxincname"] = db.name
    #opt.all_model_types = "xpress"
    
    #file1= open("/home/absolved/Documents/Bilevel_Evolution/test.gdx", "r+")
    #file2= open("output.txt", "w+")
    #base64.decode(file1,file2)
    #print(file2.read())
    db.export("/home/absolved/Documents/Bilevel_Evolution/test.gdx")
    gdx_string = ''
    with open("/home/absolved/Documents/Bilevel_Evolution/test.gdx", 'rb') as f:
        text = f.read()
        gdx_string = gdx_string + str(base64.b64encode(text))
        gdx_string = gdx_string.strip("b'")
    gams_xml= createGAMS_XML.create_xml(get_model_text(),gdx_string)
    xmlfile = open("gamstest.xml", "w+")
    xmlfile.write(gams_xml)
    xmlfile.close()
    return neosclient.send_xml()

def evaluate(individual):
    #this needs to take as input the attack vector, send the graph minus the attacked nodes to gams, solve the flow problem using gams, and then use the fitness value calculated by GAMS
    #f1 = power flow, f2 = water flow, f3 = comms flow
    #return (random.randint(0,10),random.randint(0,10),random.randint(0,10))
    if (tuple(individual) in attack_dict):
        multi_obj_value = attack_dict[tuple(individual)]
        print("attack found in dict")
    else:    
        multi_obj_value = solveGAMS(individual)
        append_attackdict(individual,multi_obj_value)
        attack_dict[tuple(individual)] = multi_obj_value
    print("Attack vector: ", individual, "objective value: ", multi_obj_value)
    return multi_obj_value

def generate_individual(attacksize,graphsize):
    #attack nodes randomly
    nodelist = [0]*graphsize
    count = 0
    attacklist = []
    while (count < attacksize):
        attack = random.randint(1,graphsize - 2)
        while(attack in attacklist):
            attack = random.randint(1,graphsize - 2) 
        nodelist[attack] = 1
        attacklist.append(attack)
        count += 1       
    return nodelist 

#performs crossover operation on 2 individuals. Here anywhere from 1 to (attacksize-1) attacks will be swapped.
def cxAttack(ind1,ind2,attacksize):
    cxsize = random.randint(1,attacksize-1)
    ind1_attacks = []
    ind2_attacks = []
    for i in range(1,len(ind1)-2):
        if ind1[i] == 1:
            if ind2[i] == 1:
                cxsize -= 1
                continue
            else:    
                ind1_attacks.append(i)
        if ind2[i] == 1:
            ind2_attacks.append(i)
    #pick cxsize indices to swap between the two individuals
    counter = 0
    while (counter < cxsize):
        #print("ind1", ind1)
        #print("ind1", ind1_attacks)
        #print("ind2", ind2)
        #print("ind2", ind2_attacks)
        swapindex1 = random.randint(0,len(ind1_attacks)-1)
        swapindex2 = random.randint(0,len(ind2_attacks)-1)
        ind1[ind1_attacks[swapindex1]] = 0
        ind1[ind2_attacks[swapindex2]] = 1
        ind2[ind2_attacks[swapindex2]] = 0
        ind2[ind1_attacks[swapindex1]] = 1
        ind1_attacks.remove(ind1_attacks[swapindex1])
        ind2_attacks.remove(ind2_attacks[swapindex2])
        counter += 1

    return ind1, ind2 

#has chance to change one element of the attack to a different one
def mutAttack(individual, indpb):
    possibleattacks = []
    attack = []
    for i in range(1,len(individual)-2):
        if individual[i] == 0:
            possibleattacks.append(i)
        else:
            attack.append(i)

    for index in attack:
       if (random.random() < indpb):
           newattackindex = random.randint(0,len(possibleattacks)-1)
           individual[index] = 0
           individual[possibleattacks[newattackindex]] = 1
           possibleattacks.remove(possibleattacks[newattackindex])           
    return individual,

def append_attackdict(individual,multiobj_sol):
    attack_file = open("attackdatabase.txt", "a+")
    attack_file.write(str(tuple(individual))+":"+str(multiobj_sol)+"\n")
    attack_file.close()

#uses a text file to populate a dictionary of attacks, based on attacks already calculated. This will significantly speed up progress as GAMS will not have to be used
#  every time
def load_attack_dict(filedatabase):
    dictfile = open(filedatabase, "r+")
    attack_dict = {}
    for line in dictfile:
        line = line.strip().split(":")
        key = tuple(map(int,line[0].strip("(").strip(")").split(",")))
        value = tuple(map(float,line[1].strip("(").strip(")").split(",")))
        attack_dict[key] = value
    dictfile.close()    
    return attack_dict    

attack_dict = load_attack_dict("attackdatabase.txt")

def main():
    #number of nodes
    GRAPH_SIZE = 16
    attack_budget = 3
    creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0, -1.0))
    creator.create("Individual", list, fitness=creator.FitnessMin)

    toolbox = base.Toolbox()
    toolbox.register("indices", generate_individual,attack_budget,GRAPH_SIZE) # Binary Vector of size IND_SIZE representing attacks
    toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.indices) # Define a specific attack. A chromosome.
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    POP_SIZE = 100
    num_gen = 40
    mutpb = 1 #mutation probability on the population level
    indpb = 1 #mutation probability on the individual level for each attack location
    cxpb = .5 #crossover probability

    print(len(attack_dict))

    stats_fit = tools.Statistics(lambda ind: ind.fitness.values)
    stats_size = tools.Statistics(len)
    mstats = tools.MultiStatistics(fitness=stats_fit, size=stats_size)
    mstats.register("avg", numpy.mean)
    mstats.register("std", numpy.std)
    mstats.register("min", numpy.min)
    mstats.register("max", numpy.max)

    toolbox.register("mate", cxAttack, attacksize = attack_budget)
    toolbox.register("mutate", mutAttack, indpb = indpb)
    toolbox.register("select", tools.selSPEA2)
    toolbox.register("evaluate", evaluate)

    numTrials = 1000
    result_file = open("evolutionary_results.txt", "a+")
    result_file.write("Number of generations="+str(num_gen)+" Population size="+str(POP_SIZE) + " Num trials =" + str(numTrials) +"\n")
    result_file.write("mutpb=" + str(mutpb) + " indpb=" + str(indpb) + " cxpb=" + str(cxpb) + "\n")
    result_file.write("num_iter opt_sol \n")
    
    for i in range(0, numTrials):
        print("Beginning trial ", i)
        pop = toolbox.population(n=POP_SIZE) 
        hof = tools.ParetoFront()
        pop, log = algorithms.eaSimpleCountandBreak(pop, toolbox, cxpb, mutpb, num_gen, stats=mstats, halloffame=hof, verbose=True)
        #solveGAMS([0,1,0,0,0,1,0,0,0,0,1,0,0,0,0,0])
        print(log)
        print(hof)
        best_sol = hof[0]
        best_obj = log.chapters['fitness'].select("min")[len(log)-1]
        num_iter = len(log)

        if (best_obj == 0):
            print("Global optimal found on iteration", num_iter, "\n")
            result_file.write(str(num_iter) + "  " + str(best_obj) +"\n")
        else:
            print("Suboptimal value of ", best_obj, "found on iteration", num_iter, "vector: ", best_sol, "\n")
            result_file.write(str(num_iter) + "  " + str(evaluate(best_sol))+ "\n")    
    result_file.close()        
main()    