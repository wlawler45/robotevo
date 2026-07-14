import os
import sys
!{sys.executable} -m pip install biopython pysam
import pysam
from Bio import SeqIO, Seq # Import Seq for creating Seq objects
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord