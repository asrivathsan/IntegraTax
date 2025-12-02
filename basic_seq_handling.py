import fileinput
import edlib
import re
from decimal import *
import parasail
from PyQt5 import QtGui, QtCore

from pdist_perpair import measurepair_distancem as cy_measurepair_distancem
try:
    CYTHON_ACCEL = True
    print ("cython")
except Exception:
    CYTHON_ACCEL = False
    print("python")
bps=['A','T','G','C','U','N','M','R','W','S','Y','K','V','H','D','B']
bps_base=['A','T','G','C']
ambiguity_codes=[("R", "A"), ("R", "G"),("M", "A"), ("M", "C"),("S", "C"), ("S", "G"),("Y", "C"), ("Y", "T"),("K", "G"), ("K", "T"),("W", "A"), ("W", "T"),("V", "A"), ("V", "C"),("V", "G"),("H", "A"),("H", "C"),("H", "T"),("D", "A"), ("D", "G"),("D", "T"), ("B", "C"),("B", "G"), ("B", "T"),("N", "A"), ("N", "G"), ("N", "C"), ("N", "T")]

PARASAIL_GAP_OPEN=10
PARASAIL_GAP_EXTEND=1
PARASAIL_MATRIX=parasail.dnafull
def set_parasail_gaps(open_penalty, extend_penalty):
    global PARASAIL_GAP_OPEN, PARASAIL_GAP_EXTEND
    PARASAIL_GAP_OPEN = int(open_penalty)
    PARASAIL_GAP_EXTEND = int(extend_penalty)

ambiguity_dict={
    "A": {"A"}, "T": {"T"}, "G": {"G"}, "C": {"C"},
    "R": {"A", "G"}, "Y": {"C", "T"}, "M": {"A", "C"},
    "K": {"G", "T"}, "S": {"G", "C"}, "W": {"A", "T"},
    "V": {"A", "C", "G"}, "H": {"A", "C", "T"},
    "D": {"A", "G", "T"}, "B": {"C", "G", "T"},
    "N": {"A", "T", "G", "C"}
}

is_match={}
for b1 in bps:
    is_match[b1]={}
    set1=ambiguity_dict.get(b1, {b1})
    for b2 in bps:
        set2=ambiguity_dict.get(b2, {b2})
        is_match[b1][b2]=not set1.isdisjoint(set2)



def convert_to_redseq(inseq,binarystr):
    outseq=''
    for i,j in enumerate(inseq):
        if binarystr[i]=='1':
            outseq+=j
    return outseq
def rev_comp(inseq):
    comps={'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G', 'N': 'N', 'M': 'K', 'R': 'Y', 'W': 'W', 'S': 'S', 'Y': 'R', 'K': 'M', 'V': 'B', 'H': 'D', 'D': 'H', 'B': 'V'}

    comp_seq=''
    for nucl in inseq:
        comp_seq=comp_seq + comps[nucl]

    return comp_seq[::-1]
def change_ext_gaps(sequence):
    start_pos, end_pos=0, 0
    for i,bp in enumerate(sequence):
        if bp in bps_base:
            start_pos=i - 1
            break
    for i,bp in enumerate(sequence[:: - 1]):
        if bp in bps_base:
            end_pos=len(sequence) - i
            break
    new_sequence="?" * (start_pos + 1) + sequence[start_pos + 1 : end_pos] + "?" * (len(sequence) - end_pos)
    return new_sequence,start_pos,end_pos

def checkmatrix(exp_len,*args):
    flag=0
    inchars_exp= bps + ["?"] + ["-"]
    for indict in args:
        if len(indict)!=0:
            for v in indict.keys():
                for bp in v:
                    if bp not in inchars_exp:
                        flag=2
                        break
    return flag



def measurepair_distancem(seq1, seq2, minoverlap):
    num_d = 0
    num_s = 0
    is_match_local = is_match 
    for i in range(len(seq1)):
        b1 = seq1[i]
        b2 = seq2[i]
        if b1 == '-' or b2 == '-' or b1 == '?' or b2 == '?':
            continue

        m1 = is_match_local.get(b1)
        if m1 is None:
            continue
        if m1.get(b2, False):
            num_s += 1
        else:
            num_d += 1
    if (num_d + num_s) <= minoverlap:
        return False
    return num_d / (num_d + num_s)


def align_score(seq1, seq2, mode="sg_stats"):
    if mode=="sg_stats":
        return parasail.sg_stats_striped_16(seq1, seq2,PARASAIL_GAP_OPEN,PARASAIL_GAP_EXTEND,PARASAIL_MATRIX)
    elif mode=="nw_stats":
        return parasail.nw_stats_striped_16(seq1, seq2,PARASAIL_GAP_OPEN,PARASAIL_GAP_EXTEND,PARASAIL_MATRIX)
    elif mode=="sg":
        return parasail.sg_striped_16(seq1, seq2,PARASAIL_GAP_OPEN,PARASAIL_GAP_EXTEND,PARASAIL_MATRIX)
    else:
        raise ValueError(f"Unknown mode {mode}")


def measurepair_distancehom(seq1,seq2,hasN1,hasN2,minoverlap):
    if not (hasN1 or hasN2):
        res=align_score(seq1, seq2, mode="sg_stats")
        if res.length == 0:
            return 1.0
        return 1.0 - (res.matches / res.length)
    res=parasail.sg_trace_striped_16(seq1,seq2,PARASAIL_GAP_OPEN,PARASAIL_GAP_EXTEND,PARASAIL_MATRIX)
    ref,qry,comp=res.traceback.ref, res.traceback.query, res.traceback.comp
    matches, eff_len=0, 0
    inside=False
    last_nonspace=-1
    for i, (a, b, c) in enumerate(zip(ref, qry, comp)):
        if not inside and c==" ":
            continue
        inside=True
        eff_len += 1
        if c=="|":
            matches += 1
        elif c == "." and (a=="N" or b=="N"):
            matches+=1
        if c != " ":
            last_nonspace=i
    if last_nonspace >= 0:
        total_cols=len(ref)
        trailing=total_cols-(last_nonspace+1)
        eff_len-=trailing
    if eff_len<=minoverlap:
        return False
    return 1.0-(matches/eff_len)

def measurepair_distancem_fastwrapper(seq1, seq2, minoverlap):
    """
    Dispatch to Cython (bytes) if available; otherwise use the pure-Python version.
    Preserve Python’s contract: return False when effective overlap <= minoverlap.
    """
    if CYTHON_ACCEL:
        d = cy_measurepair_distancem(seq1.encode("ascii"), seq2.encode("ascii"), minoverlap)
        return False if d < 0.0 else d
    return measurepair_distancem(seq1, seq2, minoverlap)


