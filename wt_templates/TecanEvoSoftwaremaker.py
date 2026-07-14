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

    def pipetteorganizer(self):
        print("hello")

    def pipetteTALPart(self,TALset):
        total_pipettes=1
        print("pipetting RVD")
        #self.get_tips(TIP_MASK=127)
        self.get_tips()
        self.current_tips_used=0
        for key in TALset.keys():
            print(key)
            for i in range(len(TALset[key])):
                colnum=i+1
                curname="TAL"+key+str(colnum)
                curwell=self.output_row+str(colnum)
                #print(curname)
                #print(curwell)
                cur=Reagent(curname, labware=self.destination_plate, wells=curwell,def_liq_class  = self.Water_wet)
                is_last = any("pFUSB" in item for item in TALset[key][i])
                if(is_last):
                    idx = next((i for i, s in enumerate(TALset[key][i]) if "pFUSB" in s), -1)
                    TALset[key][i].pop(idx-1)
                    TALset[key][i]=TALset[key][i][:idx]
                    print(TALset[key][i])
                with group("Fill plate with mixes "):
                    for RVD in range(len(TALset[key][i])):
                        total_pipettes+=1
                        if(TALset[key][i][RVD]=='Water'):
                            continue
                        elif("pFUS" in TALset[key][i][RVD]):
                            curRVDkey=TALset[key][i][RVD]
                            print(curRVDkey)
                            curRVD=self.TALReagentDict[curRVDkey]
                            with self.tips(reuse=True, drop=False):
                                curpipetteWell = curRVD.select_all()
                                #self.pick_up_tip(TIP_MASK = robot.mask_tips[1],                       # using 200 uL tips
                                #    tip_type = "DiTi 50ul Filter LiHa",arm=self.arm)
                                #self.get_tips()
                                self.aspirate_one(robot.mask_tips[0],curRVD,vol=1.0)
                                self.dispense_one(robot.mask_tips[0],cur,vol=1.0)
                                #self.drop_tips()
                                """self.transfer(from_labware_region = curpipetteWell,
                                to_labware_region   = cur.select_all(),
                                volume              = 1.0,
                                num_samples=1)"""
                            #print(curRVD.wells)
                        else:
                            curRVDkey=TALset[key][i][RVD]+str(RVD+1)
                            print(curRVDkey)
                            curRVD=self.TALReagentDict[curRVDkey]
                            with self.tips(reuse=True, drop=False):
                                curpipetteWell = curRVD.select_all()
                                #self.pick_up_tip(TIP_MASK = robot.mask_tips[1],                       # using 200 uL tips
                                #    tip_type = "DiTi 50ul Filter LiHa",arm=self.arm)
                                #self.get_tips()
                                self.aspirate_one(robot.mask_tips[0],curRVD,vol=1.0)
                                self.dispense_one(robot.mask_tips[0],cur,vol=1.0)
                                #self.drop_tips()
                                """self.transfer(from_labware_region = curpipetteWell,
                                to_labware_region   = cur.select_all(),
                                volume              = 1.0,
                                num_samples=1)"""
                            #print(TALset[key][i][RVD])
            
            self.output_row=self.increment_row(self.output_row)
        self.drop_tips()
        #print(total_pipettes)

        '''for i in range(len(RVDseq)):
            if(RVDseq[i]=='NG'):
                x=0
            elif(RVDseq[i]=='HD'):
                x=0
            elif(RVDseq[i]=='NI'):
                x=0
            elif(RVDseq[i]=='NH'):
                x=0
        '''
    def premix_enzymes(self):
        print("premixing")
    def run(self):
        self.initialize()
        
        self.arm = self.robot.cur_arm(instructions.Pipette.LiHa1)
        #m_tips = arm.n_tips

                                                     # distribute mix1 --------------
        #self.pick_up_tip(TIP_MASK = robot.mask_tips[m_tips],                       # using 200 uL tips
                            #tip_type = "DiTi 50ul Filter LiHa",
                            #arm      = arm)                                              # set_EvoMode and set_defaults() from Evo200
        self.output_row='A'
        self.check_initial_liquid_level = True
        self.show_runtime_check_list    = True
        
        num_of_samples = self.num_of_samples
        assert self.min_s <= num_of_samples <= self.max_s, "In this demo we want to set 2x num_of_samples in a 96 well plate."
        wt           = self.worktable

        self.comment('Prefill a plate with some dilutions of two master mix and Buffer Reagent for {:d} samples.'
                     .format(num_of_samples))

        #buf_cuvette   = wt.get_labware("BufferCub", labware.Trough_100ml)      # Get Labwares from the work table
        #master_mixes_ = wt.get_labware("mixes", labware.Eppendorfrack)
        """
        buf_per_sample =0
        fv = 100

        v_mix_10_100 = fv / 10                                # to be transferred from mix1_10 to mix1_100
        buf_mix_100 = fv - v_mix_10_100
        buf_per_sample += buf_mix_100

        v_mix_10 = (fv + v_mix_10_100)/10                     # to be distribute from original mix1 to mix1_10
        buf_mix_10 = (fv + v_mix_10_100) - v_mix_10
        buf_per_sample += buf_mix_10
        """
        # Define the reagents in each labware (Cuvette, eppys, etc.)
        ####YOU HAVE TO SET DEFAULT IN EVO200_f.py\
        project_root=os.getcwd()
        
        #clean = Path(raw.lstrip('\\/'))
        relative_path = Path('external\\robot_evo\\wt_templates\\')
        #210817_NoTeShake_Deck
        #relative_path = Path(r'..\\wt_templates\\210817_NoTeShake_Deck.ewt')
        full_path = project_root / relative_path 
        #self.liquid_classes=labware.LiquidClasses(full_path)
        #self.Water_wet=self.get_liquid_class("Water wet contact DiTi 50 ")
        self.my_liquid_classes = labware.LiquidClasses(full_path)
        self.Water_wet = self.my_liquid_classes.all["Water wet contact DiTi 50 "]
        wt.set_def_DiTi(labware.DiTi_50ul_SBS)
        self.worktable.set_def_DiTi(labware.DiTi_50ul_SBS)
        wt.def_DiTi_type = labware.DiTi_50ul_SBS
        rack=wt.get_DITI_series(labware.DiTi_50ul_SBS)
        print("rack")
        #print(wt.def_DiTi_type)
        self.tips_type=labware.DiTi_50ul_SBS
        #print([self.tips_type])
        #print(self.worktable.def_DiTi_type)
        self.plate_A = wt.get_labware("Pick")
        self.destination_plate=wt.get_labware("Place")
        self.TALReagentDict={}
        RVDkeys=["HD","NH","NI","NG","pFUSB"]
        pFUS_AX=['A1A','A2A','A2B','A3A','A3B','A4A','A4B']
        RVDrows={"HD":"A","NH":"B","NI":"C","NG":"D","pFUS_AX":"E","pFUSB":"F"}
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
        self.pipetteTALPart(self.TALsets)
            #self.pipetteTALPart(row)
            #print(row)
        #print(self.TALsets)
        """
        buffer = Reagent("Buffer ", buf_cuvette, volpersample   = buf_per_sample,
                                                 def_liq_class  = self.Water_wet,
                                                 num_of_samples = 2 * self.num_of_samples)

        mix1 = Reagent("mix1", master_mixes_, volpersample   = v_mix_10,
                                              def_liq_class  = self.Water_wet,
                                              num_of_samples = self.num_of_samples)

        mix2 = Reagent("mix2", master_mixes_, volpersample   = v_mix_10,
                                              def_liq_class  = self.Water_wet,
                                              num_of_samples = self.num_of_samples)
        """
        # Show the check_list GUI to the user for possible small changes

        #self.check_list()

        
        """
        plate1 = wt.get_labware("plate1", '96 Well Microplate')
        plate2 = wt.get_labware("plate2", '96 Well Microplate')

        new_location = wt.get_labware("plate2-moved").location

        Reagent.use_minimal_number_of_aliquots = False           # Define derived reagents  ---------------------

        mix1_10 = Reagent(f"mix1, diluted 1:10",
                          plate1,
                          initial_vol = 0.0,
                          num_of_aliquots= num_of_samples,
                          def_liq_class = self.Water_free,
                          excess      = 0)

        mix2_10 = Reagent(f"mix2, diluted 1:10",
                          plate2,
                          initial_vol = 0.0,
                          num_of_aliquots= num_of_samples,
                          def_liq_class = self.Water_free,
                          excess      = 0)

        mix1_100 = Reagent(f"mix1, diluted 1:100",
                           plate1,
                           wells       = 'A07',
                           initial_vol = 0.0,
                           num_of_aliquots= num_of_samples,
                           def_liq_class = self.Water_free,
                           excess      = 0)

        mix2_100 = Reagent(f"mix2, diluted 1:100",
                           plate2,
                           wells       = 'A07',
                           initial_vol = 0.0,
                           num_of_aliquots= num_of_samples,
                           def_liq_class = self.Water_free,
                           excess      = 0)

        instructions.transfer_rack(plate2, new_location).exec()                  # just showing how RoMa works.

        with group("Fill plate with mixes "):

            self.user_prompt("Put the plates for Buffer ")

            with self.tips(reuse=True, drop=False):
                self.distribute(reagent           = mix1,
                                to_labware_region = mix1_10.select_all())

            with self.tips(reuse=True, drop=False):
                self.distribute(reagent           = mix2,
                                to_labware_region = mix2_10.select_all())

            with self.tips(reuse=True, drop=False):
                self.distribute(reagent=buffer, to_labware_region=mix1_10.select_all(), volume=buf_mix_10)
                self.distribute(reagent=buffer, to_labware_region=mix2_10.select_all(), volume=buf_mix_10)

            with self.tips(reuse=True, drop=False):
                wells_100 = mix1_100.select_all()
                self.transfer(from_labware_region = mix1_10.select_all(),
                              to_labware_region   = wells_100,
                              volume              = v_mix_10_100)

            with self.tips(reuse=True, drop=False):
                wells_100 = mix2_100.select_all()
                self.transfer(from_labware_region = mix2_10.select_all(),
                              to_labware_region   = wells_100,
                              volume              = v_mix_10_100)

            with self.tips(reuse=True, drop=False):
                self.distribute(reagent=buffer, to_labware_region=mix1_100.select_all(), volume=buf_mix_100)
                self.distribute(reagent=buffer, to_labware_region=mix2_100.select_all(), volume=buf_mix_100)

            self.drop_tips()
        """
        self.done()


if __name__ == "__main__":
    
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
    #raw="/external/robot_evo/wt_templates/AddLiquidtoPCRTubesWL.ewt"
    #clean = Path(raw.lstrip('\\/'))
    relative_path = Path('external\\robot_evo\\wt_templates\\AddLiquidtoPCRTubesWL.ewt')
    #210817_NoTeShake_Deck
    #relative_path = Path(r'..\\wt_templates\\210817_NoTeShake_Deck.ewt')
    full_path = project_root / relative_path 
    p = TALEmix(num_of_samples= 1,
                     run_name= "_4s_mix_1_2",worktable_template_filename=full_path,TAL_CSV_filename="yarrowia_targeter25.csv")

    p.use_version('No version')
    # p.set_first_tip('A01')
    p.run()