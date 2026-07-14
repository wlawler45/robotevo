import csv
import sys
from pathlib import Path
import os
import logging
# Automatically finds the 'external/repo_name' folder relative to this file
sys.path.append(str(Path(__file__).parent / "external" / "robot_evo"))
print(sys.path)

from protocols.evo200_f.evo200_f import *
import EvoScriPy.labware as labware
from EvoScriPy.protocol_steps import *
import EvoScriPy.labware as labware

class TALEmix(Evo200_FLI):
    """
    Prepare two 1:10 serial dilutions of two different mixes each in 'n' 100 uL final volume wells
    (each in a microplate, the second one to be moved to the working position).

    'mix1' and 'mix2' are diluted separately in n wells 1:10 (mix1_10 and mix2_10 respectively) using
    a provided "buffer". From those wells a portion is transferred to the final 1:100 dilutions
    (mix1_100 and mix2_100 respectively) to fv=100 uL final volume

    One way to achieve this:
    - Calculate how much to transfer from each mix1_10 to mix1_100. v_mix1_10_100= fv/10 and from diluent.
    - Calculate how much to distribute from mix1 to each mix1_10 and from diluent.
    - Define a reagent `mix1` and `mix2`in an Eppendorf rack (labware) for the calculated volume per "sample" (mix1_10 or 2).
    - Define a reagent `buffer` in a 100 mL cubette `BufferCub` for the total volume per "sample".
    - Generate check list
    - Transfer plate 2 from the original location `plate2` to the final location `plate2-moved`
    - Define derived reagents for diluted mixes
    - Distribute mix1 and buffer into mix1_10 and similar with mix2
    - Transfer from mix1_10 to mix1_100 and distribute buffer here. The same with mix2_10
    """

    name = "Prefill one plate with Buffer."
    min_s, max_s = 1, 96/2

    # for now just ignore the variants
    def def_versions(self):
        self.versions = {'No version': self.V_def}

    def V_def(self):
        pass

    def __init__(self,
                 GUI                         = None,
                 num_of_samples: int         = None,
                 worktable_template_filename = None,
                 output_filename             = None,
                 first_tip                   = None,
                 run_name: str               = "",
                 TAL_CSV_filename:str        = ""):

        this = Path(__file__).parent
        self.TAL_CSV_filename=TAL_CSV_filename
        Evo200_FLI.__init__(self,
                            GUI                         = GUI,
                            num_of_samples              = num_of_samples or DemoTwoMixes.max_s,
                            worktable_template_filename = worktable_template_filename or
                                                          this / 'demo-two.mixes.Evo200example.ewt',
                            output_filename             = output_filename or this /'external'/ 'robot_evo'/ 'protocols'/ 'TALtester',
                            first_tip                   = first_tip,
                            run_name                    = run_name)

    def increment_row(self,c):
        print("incrementing")
        return chr(ord(c) + 1) if c != 'Z' else 'A'
    
    def masker(self,pipettes_needed):
        print("bobi info")
        print(pipettes_needed)
        if(pipettes_needed!=1):
            return (2**pipettes_needed)-1
        else:
            return 1
    def add_enzymes(self,enzyme,volume):
        for key in self.cur_dest_dict.keys():
            self.get_tips(TIP_MASK=1)
            cur=self.cur_dest_dict[key]
            self.aspirate_one(robot.mask_tips[0],enzyme,vol=volume)
            self.dispense_one(robot.mask_tips[0],cur,vol=volume)
            self.drop_tips()

    def pipetteorganizer(self,cur_array,num_pipettes):

        #print(cur_array)
        mask=self.masker(num_pipettes)
        #print(mask)
        self.get_tips(TIP_MASK=mask)
        
        for i in range(len(cur_array)):
            #print(i)
            self.mix_one(i,cur_array[i][0],vol=5.0,cycles=3)
            self.aspirate_one(i,cur_array[i][0],vol=1.0)
            #self.aspirate_one(robot.mask_tips[i+1],cur_array[i][0],vol=1.0)
        
                    
        for k in range(len(cur_array)):
            self.dispense_one(k,cur_array[k][1],vol=1.0)
        self.drop_tips()
        #for entry in cur_array:

        self.cur_array=[]

    def initial_water_add(self,TALset):
        self.cur_dest_dict={}
        self.get_tips(TIP_MASK=1)
        for key in TALset.keys():
            print(key)
            for i in range(len(TALset[key])):
                
                colnum=i+1
                curname="TAL"+key+str(colnum)
                curwell=self.output_row+str(colnum)
                print(curname)
                print(curwell)
                cur_dest=Reagent(curname, labware=self.destination_plate, wells=curwell,def_liq_class  = self.Water_wet)
                self.cur_dest_dict[curname]=cur_dest
                is_last = any("pFUSB" in item for item in TALset[key][i])
                last_water=9
                if(is_last):
                    idx = next((i for i, s in enumerate(TALset[key][i]) if "pFUSB" in s), -1)
                    TALset[key][i].pop(idx-1)
                    TALset[key][i]=TALset[key][i][:idx]
                    last_water=16-len(TALset[key][i])
                    
                with group("Add water to all"):
                    
                    
                    
                    self.aspirate_one(robot.mask_tips[0],self.water,vol=last_water)
                    self.dispense_one(robot.mask_tips[0],cur_dest,vol=last_water)
            
            self.output_row=self.increment_row(self.output_row)
        self.drop_tips()
        


    def pipetteTALPart(self,TALset):
        total_pipettes=1
        print("pipetting RVD")
        #self.get_tips(TIP_MASK=127)
        #self.get_tips()
        self.current_tips_used=0
        self.cur_dest=None
        self.cur_array=[]
        for key in TALset.keys():
            print(key)
            for i in range(len(TALset[key])):
                colnum=i+1
                curname="TAL"+key+str(colnum)
                curwell=self.output_row+str(colnum)
                #print(curname)
                #print(curwell)
                #self.cur_dest=Reagent(curname, labware=self.destination_plate, wells=curwell,def_liq_class  = self.Water_wet)
                cur=self.cur_dest_dict[curname]
                is_last = any("pFUSB" in item for item in TALset[key][i])
                if(is_last):
                    idx = next((i for i, s in enumerate(TALset[key][i]) if "pFUSB" in s), -1)
                    TALset[key][i].pop(idx-1)
                    TALset[key][i]=TALset[key][i][:idx]
                    print(TALset[key][i])
                with group("Fill plate with mixes "):
                    for RVD in range(len(TALset[key][i])):
                        
                        if(TALset[key][i][RVD]=='Water'):
                            continue
                        elif("pFUS" in TALset[key][i][RVD]):
                            curRVDkey=TALset[key][i][RVD]
                            print(len(self.cur_array))
                            curRVD=self.TALReagentDict[curRVDkey]
                            self.cur_array.append([curRVD,cur])
                            #with self.tips(reuse=True, drop=False):
                                #curpipetteWell = curRVD.select_all()
                                #self.pick_up_tip(TIP_MASK = robot.mask_tips[1],                       # using 200 uL tips
                                #    tip_type = "DiTi 50ul Filter LiHa",arm=self.arm)
                                #self.get_tips()
                            #    self.aspirate_one(robot.mask_tips[0],curRVD,vol=1.0)
                            #    self.dispense_one(robot.mask_tips[0],cur,vol=1.0)
                                #self.drop_tips()
                                
                            #print(curRVD.wells)
                        else:
                            curRVDkey=TALset[key][i][RVD]+str(RVD+1)
                            print(len(self.cur_array))
                            curRVD=self.TALReagentDict[curRVDkey]
                            self.cur_array.append([curRVD,cur])
                            #with self.tips(reuse=True, drop=False):
                                #curpipetteWell = curRVD.select_all()
                                #self.pick_up_tip(TIP_MASK = robot.mask_tips[1],                       # using 200 uL tips
                                #    tip_type = "DiTi 50ul Filter LiHa",arm=self.arm)
                                #self.get_tips()
                            #    self.aspirate_one(robot.mask_tips[0],curRVD,vol=1.0)
                            #    self.dispense_one(robot.mask_tips[0],cur,vol=1.0)
                                #self.drop_tips()
                                
                            #print(TALset[key][i][RVD])
                        if(len(self.cur_array)==8):
                            print("-------------------------------Triggered")
                            self.pipetteorganizer(self.cur_array,8)
            #self.output_row=self.increment_row(self.output_row)
        self.pipetteorganizer(self.cur_array,len(self.cur_array))
        #self.drop_tips()
        #print(total_pipettes)

    def premix_enzymes(self):
        print("premixing")
    def run(self):
        self.initialize()
        
        self.arm = self.robot.cur_arm(instructions.Pipette.LiHa1)

        self.output_row='A'
        self.check_initial_liquid_level = True
        self.show_runtime_check_list    = True
        wt           = self.worktable

        self.comment('Prefill a plate with some dilutions of two master mix and Buffer Reagent for {:d} samples.'
                     .format(num_of_samples))

        #buf_cuvette   = wt.get_labware("BufferCub", labware.Trough_100ml)      # Get Labwares from the work table
        #master_mixes_ = wt.get_labware("mixes", labware.Eppendorfrack)

        # Define the reagents in each labware (Cuvette, eppys, etc.)
        ####YOU HAVE TO SET DEFAULT Tip type IN EVO200_f.py, you CANNOT set it here, it won't work
        project_root=os.getcwd()
        
        #clean = Path(raw.lstrip('\\/'))
        relative_path = Path('external\\robot_evo\\wt_templates\\')
        #210817_NoTeShake_Deck
        #relative_path = Path(r'..\\wt_templates\\210817_NoTeShake_Deck.ewt')
        full_path = project_root / relative_path 
        #self.liquid_classes=labware.LiquidClasses(full_path)
        #self.Water_wet=self.get_liquid_class("Water wet contact DiTi 50 ")
        self.my_liquid_classes = labware.LiquidClasses(full_path)
        self.Water_wet = self.my_liquid_classes.all["Water free dispense DiTi 50 filter"]

        #Specify the names of your plates here, they must match the names you gave them in Evoware
        self.plate_A = wt.get_labware("Pick")
        self.destination_plate=wt.get_labware("Place")
        #self.destination_plate=wt.get_labware("PCR-place-WL")
        self.TALReagentDict={}
        RVDkeys=["HD","NH","NI","NG","pFUSB"]
        pFUS_AX=['A1A','A2A','A2B','A3A','A3B','A4A','A4B']
        RVDrows={"HD":"A","NH":"B","NI":"C","NG":"D","pFUS_AX":"E","pFUSB":"F"}
        self.water=Reagent("water", labware=self.plate_A, wells="G1",def_liq_class  = self.Water_wet,min_vol=100.0, initial_vol=100.0)
        for key in RVDkeys:

            for i in range(1,7):
                curname=key+str(i)
                curwell=RVDrows[key]+str(i)
                #print(curname)
                #print(curwell)
                cur=Reagent(curname, labware=self.plate_A, wells=curwell,def_liq_class  = self.Water_wet,min_vol=100.0, initial_vol=100.0)

                
                self.TALReagentDict[curname] = cur

        for i in range(1,8):
            curname="pFUS_"+pFUS_AX[i-1]
            curwell=RVDrows["pFUS_AX"]+str(i)
            #print(curname)
            #print(curwell)
            cur=Reagent(curname, labware=self.plate_A, wells=curwell,def_liq_class  = self.Water_wet,min_vol=100.0, initial_vol=100.0)
            self.TALReagentDict[curname] = cur

        file2=open(self.TAL_CSV_filename,'r',newline='\n')
        self.csvreader=csv.reader(file2)
        counter=1
        skip=True
        currentTal=None
        self.TALsets={}
        instructions.wash_tips(wasteVol=5, FastWash=True).exec()
        for row in self.csvreader:
            if("sequence" in row[0]):
                print("started")
                skip=True
                
                if(currentTal==None):
                    currentTal='Left'
                    
                else:
                    currentTal='Right'
                continue

            if(skip):
                skip=False
                continue
            
            if("=150" in row[0]):
                counter+=1
                continue
            self.TALsets.setdefault(currentTal,[]).append(row)
        
        print(self.TALReagentDict.keys())
        self.initial_water_add(self.TALsets)
        self.pipetteTALPart(self.TALsets)

        self.done()


if __name__ == "__main__":
    #For troubleshooting you can uncomment these lines to generate a logging file named robotevo.log
    """
    logging.basicConfig(
        level=logging.DEBUG,           # capture everything, not just warnings
        format='%(levelname)s:%(name)s:%(message)s',
        handlers=[
            logging.FileHandler('robotevo.log'),  # write to file
            logging.StreamHandler()               # also keep printing to terminal
        ]
    )
    """
    print(labware.__file__)
    project_root=os.getcwd()

    #This should be the path to your workspace file, this should match the file on the Tecan machine
    relative_path = Path('external\\robot_evo\\wt_templates\\AddLiquidtoPCRTubesWL.ewt')
    #This is the output filename that will be used to save your files
    run_name="_4s_mix_1_2_mixing"
    #The CSV file containing the TALE sequence generated by the current Colab and python output scripts, it does rely on the current formatting for correct parsing
    TAL_CSV_filename="yarrowia_targeter25.csv"
    full_path = project_root / relative_path 
    p = TALEmix(num_of_samples= 1,
                     run_name= run_name,worktable_template_filename=full_path,TAL_CSV_filename=TAL_CSV_filename)

    p.use_version('No version')
    # p.set_first_tip('A01')
    p.run()
    