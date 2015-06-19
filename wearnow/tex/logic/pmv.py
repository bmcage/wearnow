#calculate clothing area factor (fcl)

Icl=0.5 # assumed clothing insulation value

if Icl<=0.078:
    fcl=1+1.290*Icl
else:
    fcl=1.05+0.645*Icl
    
#print(fcl)
    
    
#calculate convective heat transfer coefficient (hc)
    
Vr=2.5  # relative air velocity assumed

import math
if 12.1< (math.sqrt(Vr)):
    hc=2.38*abs(tcl-ta)**0.25
else:
    hc=12.1*math.sqrt(Vr)
    
print(hc)
    
ta=25 # air temp assumed in C

def kelvin(ta):
    tk=ta+273.15
    return tk

M=55 #assumed metabolic rate


# calculate initial value of clothing temperature(tcl) for iterations
tcl_previous=kelvin(ta)+((35.5-ta)/(3.5*Icl+0.1))

#tcl=(35.7-0.028*(M-Icl)*((3.96e-8)*(fcl))*((tcl_previous+273.15)**4-(ta+273.15)**4)
#    +(fcl*hc*(tcl_previous-ta)))

#calculate final value of  clothing temperature
from scipy.optimize.nonlin import broyden1
def rootfn(tcl) :
    return (35.7-0.028*M-Icl*((3.96e-8)*fcl*((tcl+273.15)**4-(ta+273.15)**4)
            +(fcl*hc*(tcl-ta))) ) - tcl
    
tcl = broyden1(rootfn, tcl_previous, f_tol=1e-10)
tcl = float(tcl)
print (tcl, rootfn(tcl))

# calculate skin temperature
def skin_temp(M=55):
    tsk = 35.7-0.028*(M)
    return tsk
    
# calculate partial vapor pressure
    
ta=25
a=(16.6536-(4030.183/(ta+235))) #see signs
   
def sat_pressure (ta):
    import math
    ps=math.exp(a)
    return ps
    print (ps)

def partial_pressure(ps,RH=(50)):
    pa=10*RH*ps
    return pa
    print (pa)

    