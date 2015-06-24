import math
#calculate clothing area factor (fcl)

#Environmental Variables 
va=0.05 # condition for static body and still wind

#calculate time weighted average of Metabolic rate (need to be defined in profile)
AppData = {
 'activity': 'At rest,sitting',
 'ensemble': { 'insulation': [4,2],
               'vapresist' : [3,4],
               'garmtype'  : ['trouser', 'pull'],
             },
 'climate': {'ta': 25, 'RH': 50},
}


Segment = {
    'Both hands light':70,
    'Both hands medium':85,
    'Both hands heavy':95, 
    'One arm light':90, 
    'One arm medium':110,
    'One arm heavy':130,
    'Both arms light':120,
    'Both arms medium':140, 
    'Both arms heavy':160,
    'Whole body light':180, 
    'Whole body medium':245, 
    'Whole body heavy':335,
    }

#print(Segment)
    
    #dictionary for Metabolic rate of body posture

Posture = {
    'Sitting':0,
    'Kneeling':10,
    'Crouching':10,
    'Standing':15,
    'Standing stoopped':20,
    }

#print (Posture)
    
    #dictionary for Metabolic rate of general activities

Activity = {
    'Sleeping':40,
    'Reclining':45,
    'At rest,sitting':55,
    'At rest,standing':70,
    'Car driving':80,
    'Teacher':95,
    'Walking on level even path at 2km/h':110,
    'Walking on level even path at 3km/h':140,
    'Walking on level even path at 4km/h':165,
    'Sedentary activity(office,dwelling,school,laboratory)':70,
    'Standing light activity(shopping,laboratory,light industry)':95,
    'Standing, medium activity(shop assitant,domestic work,machine work)':115,
    'Working with a handtool (light polishing)':100,
    'Working with a handtool (medium polishing)':160,
    'Working with a handtool (heavy drilling)':230,
    'Working on a machine tool(light adjustments)':100,
    'Working on a machine tool(medium loading)':140,
    'Working on a machine tool(heavy)':210,
    'Carpentry work': 220,
    'climbing ladder(11.2m/min)':290
}


# calculate partial vapor pressure
def sat_pressure (ta):
    a=(16.6536-(4030.183/(ta+235))) #see signs

    ps=math.exp(a)
    return ps
    
#print ('test sat pres 25=',sat_pressure(25))

def partial_pressure(ta, RH=(50)):
    pa=10*RH*sat_pressure(ta)
    print (pa)
    return pa
    
#print ('test par pres 25=',partial_pressure(25))



def calc_pmv (M,pa,fcl,tcl,ta,hc,Icl):
    print ('input pmv:', M,pa,fcl,tcl,ta,hc,Icl)
    hl2 = 0.42* (M-58.15)
    if M < 58.15:
        hl2 = 0
    pmv=(0.303*math.exp(-0.036*M)+0.028)*(M-3.05e-3*(5733-6.99*M-pa)-hl2\
    -(1.7e-5)*M*(5867-pa)-0.0014*M*(34-ta)-3.96e-8*fcl*((tcl+273)**4\
    -(ta+273)**4)-fcl*hc*(tcl-ta))
    return pmv

def calc_fcl(Icl):
    if Icl<=0.078:
        fcl=1+1.290*Icl
    else:
        fcl=1.05+0.645*Icl
    return fcl

def calc_Re(hc,Icl):
    # Estimation of clothing vapor resistance            
    Re=60*(1/hc+0.344*Icl)  
    return Re
    
#print(fcl)
    
    
#calculate convective heat transfer coefficient (hc)
def calc_hc(Vr,tcl,ta):    
    if 12.1< (math.sqrt(Vr)):
        hc=2.38*abs(tcl-ta)**0.25
    else:
        hc=12.1*math.sqrt(Vr)
    return hc
    
def kelvin(ta):
    tk=ta+273.15
    return tk

#calculation of relative air velocity (m/s)
def calc_Vr(M):
    return 0.1
    if M<58.2:      # metabolic rate in W/m2*
        v_ar=0
    else:
        v_ar=(M-1)*0.3
    return v_ar

def calc_Icl(ensembledata):
    Icl = 0
    for I, Vres, Gt in zip(ensembledata['insulation'], 
                   ensembledata['vapresist'],
                   ensembledata['garmtype']):
        Icl += I
    return Icl

# calculate skin temperature
#def skin_temp(M=55):
#    tsk = 35.7-0.028*(M)
#    return tsk

def calc_tcl_OLD(ta,Icl,M,fcl,hc):
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
    
    #calculate initial value for tcl
def calc_tcl_previous(ta,Icl):
    # calculate initial value of clothing temperature(tcl) for iterations
    tcl_previous=kelvin(ta)+((35.5-ta)/(3.5*Icl+0.1))
    return tcl_previous
    
#print ('start tcl', calc_tcl_previous(ta,Icl))
    
def calc_tcl(ta,Icl,fcl,M):
    
    # hc for forced convection
    def calc_hcf (vr=0.1): 
        hcf=12.1*math.sqrt(vr)
        return hcf
      
    P1=Icl*fcl
    P2=P1*3.96
    P3=P1*100
    P4=P1*kelvin(ta)
    P5=308.7*0.028*M+P2*(kelvin(ta)/100)*4
    XN=(calc_tcl_previous(ta,Icl))/100
    XF=XN
    conv_point=0.00015

    cond = True
    conv = False
    it = 0
    while cond:
        it += 1
        XF=(XF+XN)/2
        HCN=2.38*abs(100*XF-kelvin(ta))**0.25
      
        if calc_hcf(vr=0.1)>HCN:
            HC=calc_hcf(vr=0.1)
        else:
            HC=HCN
        
        XN=(P5+P4*HC-P2*XF**4)/(100+P3*HC)
        tcl=100*XN-273
      
        if abs(XN-XF)>conv_point:
            cond=True
        else:
            cond=False
            conv = True
        if it > 150:
            #too long to converge
            cond = False
        print ('calc', it, tcl,XN, XF, conv)
        
    return tcl
       
        
#tcl = calc_tcl(ta,Icl,fcl,M)

#print ('final tcl', tcl)
    
    
    
def calc_comfort(appdata):
    ta = appdata['climate']['ta']
    RH = appdata['climate']['RH']
    
    #M = Activity[appdata['activity']]
    M = appdata['activity']
    Icl = calc_Icl(appdata['ensemble'])
    fcl = calc_fcl(Icl)
    Vr = calc_Vr(M)
    tcl = calc_tcl(ta,Icl,fcl,M)
    hc = calc_hc(Vr,tcl,ta)
    pa = partial_pressure(ta, RH)
    
    return calc_pmv (M,pa,fcl,tcl,ta,hc,Icl)

    



##Calculation of Metaboilc rate (W/m2)
#Mb= 45               #basal metabolic rate
#
#comf = calc_comfort(AppData)


#dictionary for Metabolic rate of body segment involed


#Wetting comfort as an additional criterion

def calc_wetability (Re,M,pa): #Re value here is for the vapor resistance of ensemble
    
    w=(0.42*(M-58)*Re/(5770-7.2*M-pa))+0.06
    return w
    if w<0.0012*M+0.15:
        print("comfortable for wetting")
    else:
        print("uncomfortable for wetting")


if __name__ == "__main__": 
    #test to determine if our comfort function works
    ta=19
    Icl=.155 #0.5
    M=1.2*58.2
    vr=0.1
    RH=40

    fcl = calc_fcl(Icl)
    Vr = calc_Vr(M)
    Vr = 0.1
    print ('relvel', Vr,vr)
    tcl = calc_tcl(ta,Icl,fcl,M)
    hc = calc_hc(Vr,tcl,ta)
    pa = partial_pressure(ta, RH)
    
    
    print('pmv', calc_pmv (M,pa,fcl,tcl,ta,hc,Icl))
    print ('input pmv 1:', calc_pmv(69.84, 878.488083014345, 1.149975, 99.8658516518887, 19, 3.826355968803739, 0.155))
    print ('input pmv 2:', calc_pmv(69.84, 878.488083014345, 1.149975, 22.8658516518887, 19, 3.826355968803739, 0.155))
    print ('input pmv 3:', calc_pmv(69.84, 878.488083014345, 1.149975, 99.8658516518887, 19, 3.826355968803739, 0.155))
#calc_wetability (Re=0.015, M=55, pa=25)



#def something():

    
    
    #def var1 = 'Sleeping'
    
    
    #sum = Segment[var1] + Posture[var2] + Activity[var3]
    #returns sum

#superdictionary = {
#    'person': {
#        'age': 20,
#        'location': 'BELGIUM'
#    },
#    'person2': [20, 'BELGIUM']
#}

#return pmv

#pmv = 1+1
#pmv = pmv / 5
#pmv = pmv 