from PyQt5 import QtWidgets, QtCore
from urllib.parse import quote
from PyQt5.QtCore import Qt
from PyQt5 import QtGui
import sys,queue
from pathlib import Path
import os,logging
import fileinput
import basic_seq_handling as bsm
import clustering_functions as clust
from collections import defaultdict
import re,threading
import platform, ctypes
from decimal import *
import time,signal
import json
import copy
import webbrowser
import edlib
import subprocess
import time, datetime
import parasail
import multiprocessing as mp
mp.set_start_method("spawn", force=True)
import heapq,contextlib
import shutil
import runpy
import traceback
from collections import OrderedDict
import struct
import pickle
import faulthandler

faulthandler.enable()

progress_value_g=None
progress_lock_g=None
write_queues_g=[]
n_writers_g=1
cancel_flag_g=None
BIN_SCALE=10000
RADIX_BUCKETS=128
BUCKET_WIDTH=(BIN_SCALE+1+RADIX_BUCKETS - 1) // RADIX_BUCKETS  
def _radix_stage1_partition_from_workers(pdistdir):
    ws_dir  =os.path.join(pdistdir, "worker_streams")
    out_root=os.path.join(pdistdir, "radix_merged")
    os.makedirs(out_root, exist_ok=True)

    try:
        worker_files=sorted(f for f in os.listdir(ws_dir)
                              if f.startswith("worker_") and f.endswith(".bin"))
    except FileNotFoundError:
        worker_files=[]
    if not worker_files:
        return
    BUF=8*1024*1024
    open_fhs={}
    def get_bucket_fh(bucket_id: int):
        fh=open_fhs.get(bucket_id)
        if fh is None:
            path=os.path.join(out_root, f"bucket_{bucket_id:03d}.bin")
            fh=open(path, "ab", buffering=8*1024*1024)
            open_fhs[bucket_id]=fh
        return fh
    for wf in worker_files:
        wpath=os.path.join(ws_dir, wf)
        with open(wpath, "rb", buffering=BUF) as f:
            while True:
                hb=f.read(2)
                if not hb:
                    break
                if len(hb)<2:
                    break
                n_bins=struct.unpack("<H", hb)[0]
                if n_bins==0:
                    continue

                tbl=f.read(n_bins*6)
                if len(tbl)<n_bins*6:
                    break

                bids, lens=[], []
                off=0
                for _ in range(n_bins):
                    bid=struct.unpack_from("<H", tbl, off)[0]; off+=2
                    ln =struct.unpack_from("<I", tbl, off)[0]; off+=4
                    bids.append(bid); lens.append(ln)

                payloads=[]
                for ln in lens:
                    data=f.read(ln)
                    if not data: data=b""
                    payloads.append(data)
                by_bucket={}
                for bid, data in zip(bids, payloads):
                    bucket_id=bid // BUCKET_WIDTH
                    by_bucket.setdefault(bucket_id, []).append((bid, data))
                for bucket_id, items in by_bucket.items():
                    fh_out=get_bucket_fh(bucket_id)
                    hdr=bytearray()
                    hdr.extend(struct.pack("<H", len(items)))
                    for bid, data in items:
                        hdr.extend(struct.pack("<HI", bid, len(data)))
                    fh_out.write(hdr)
                    for _, data in items:
                        fh_out.write(data)
    for fh in list(open_fhs.values()):
        try:
            fh.flush(); os.fsync(fh.fileno())
        except Exception:
            pass
        try:
            fh.close()
        except Exception:
            pass
    try:
        shutil.rmtree(ws_dir, ignore_errors=True)
    except Exception:
        pass

def _radix_stage2_demux_to_pmatrix(pdistdir, lru_cap=96):
    merged_root=os.path.join(pdistdir, "radix_merged")
    try:
        merged_files=sorted(f for f in os.listdir(merged_root)
                              if f.startswith("bucket_") and f.endswith(".bin"))
    except FileNotFoundError:
        merged_files=[]
    if not merged_files:
        return
    BUF=8*1024*1024
    out_LRU=OrderedDict()
    def get_out(bid: int):
        key=f"{bid / 100:.2f}" 
        fh=out_LRU.pop(key, None)
        if fh is None:
            if len(out_LRU) >= lru_cap:
                _, oldfh=out_LRU.popitem(last=False)
                try: oldfh.close()
                except: pass
            path=os.path.join(pdistdir, key)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            fh=open(path, "ab", buffering=1024*1024)
        out_LRU[key]=fh
        return fh
    for mf in merged_files:
        with open(os.path.join(merged_root, mf), "rb", buffering=BUF) as f:
            while True:
                hb=f.read(2)
                if not hb:
                    break
                if len(hb)<2:
                    break
                n_bins=struct.unpack("<H", hb)[0]
                if n_bins==0:
                    continue
                tbl_bytes=f.read(n_bins*6)
                if len(tbl_bytes)<n_bins*6:
                    break
                table=[]
                off=0
                for _ in range(n_bins):
                    bid=struct.unpack_from("<H", tbl_bytes, off)[0]; off+=2
                    ln =struct.unpack_from("<I", tbl_bytes, off)[0]; off+=4
                    table.append((bid, ln))
                for bid, ln in table:
                    remaining=ln
                    out=get_out(bid)
                    while remaining:
                        chunk=f.read(BUF if remaining>BUF else remaining)
                        if not chunk:
                            remaining=0
                            break
                        out.write(chunk)
                        remaining-=len(chunk)
    for _, fh in list(out_LRU.items()):
        try: fh.close()
        except: pass
    try:
        shutil.rmtree(merged_root, ignore_errors=True)
    except Exception:
        pass
def _pair_batches(keys, bsize):
    batch=[]
    n=len(keys)
    for i in range(n):
        k1=keys[i]
        for j in range(i+1, n):
            batch.append((k1, keys[j]))
            if len(batch) >= bsize:
                yield batch
                batch=[]
    if batch:
        yield batch

def _run_balanced_pool(pool, batches_iter, submit_fn, on_progress, max_inflight):
    inflight=[]
    for _ in range(max_inflight):
        try:
            b=next(batches_iter)
        except StopIteration:
            break
        inflight.append(submit_fn(b))
    while inflight:
        progressed=False
        for r in inflight[:]:
            if r.ready():
                res=r.get() 
                inflight.remove(r)
                on_progress(res) 
                try:
                    b=next(batches_iter)
                except StopIteration:
                    continue
                inflight.append(submit_fn(b))
                progressed=True
        if not progressed:
            time.sleep(0.05)
import os, struct, pickle
from collections import defaultdict

def _bucket_of_bid(bid: int) -> int:
    return bid // BUCKET_WIDTH

def _worker_batch_flatstream(args):
    (batch, minoverlap, mode, pdistdir, TICK_STEP, DUMP_EVERY, total_pairs)=args

    seqdict1 =seqdict1_g
    seqiddict=seqiddict_g
    hasn     =hasn_g
    pid      =os.getpid()

    from collections import defaultdict
    bins=defaultdict(list)

    tick=0
    for seq, remseq in batch:
        if mode=="hom":
            dist=bsm.measurepair_distancehom(seq, remseq, hasn[seq], hasn[remseq], minoverlap)
        else:
            dist=bsm.measurepair_distancem_fastwrapper(seq, remseq, minoverlap)

        tick+=1
        if tick>=TICK_STEP:
            tick=0

        if dist is False:
            ids1=[seqiddict[x] for x in seqdict1[seq]]
            ids2=[seqiddict[x] for x in seqdict1[remseq]]
            tmp_err=os.path.join(pdistdir, "tmp", f"overlap_{pid}.tsv")
            os.makedirs(os.path.dirname(tmp_err), exist_ok=True)
            with open(tmp_err, "a") as efh:
                efh.write(f"{ids1}\t{ids2}\n")
            continue

        bid=int(round(dist*BIN_SCALE)) 
        if bid<0: bid=0
        if bid>BIN_SCALE: bid=BIN_SCALE

        bins[bid].append(f"{seqdict1[seq][0]}\t{seqdict1[remseq][0]}\n")

    if not bins:
        return {"pid": pid, "total_pairs": len(batch)}
    ws_dir=os.path.join(pdistdir, "worker_streams")
    os.makedirs(ws_dir, exist_ok=True)
    stream_path=os.path.join(ws_dir, f"worker_{pid}.bin")
    bids_sorted=sorted(bins.keys())
    header=bytearray()
    payloads=[]
    header.extend(struct.pack("<H", len(bids_sorted))) 
    for bid in bids_sorted:
        payload="".join(bins[bid]).encode("utf-8")
        payloads.append(payload)
        header.extend(struct.pack("<HI", bid, len(payload))) 
    with open(stream_path, "ab", buffering=8*1024*1024) as fh:
        fh.write(header)
        for payload in payloads:
            fh.write(payload)
    return {"pid": pid, "total_pairs": len(batch)}

if getattr(sys, 'frozen', False) and platform.system()=='Windows':
    res_dir=os.path.join(sys._MEIPASS, "Resources")
    os.environ["PATH"]=res_dir+os.pathsep+os.environ.get("PATH", "")
    try:
        os.add_dll_directory(res_dir)  
    except Exception:
        pass
def platform_scaled_stylesheet(path):
    with open(path, "r", encoding="utf-8") as f:
        qss=f.read()
    if platform.system()=="Darwin": 
        qss=qss.replace("10pt", "12pt")
        qss=qss.replace("11pt", "13pt")
        qss=qss.replace("12pt", "14pt")
        qss=qss.replace("13pt", "15pt")
    elif platform.system()=="Windows":
        qss=qss.replace("10pt", "10pt")
    return qss
class DistanceStarter(QtCore.QThread):
    progressUpdated    =QtCore.pyqtSignal(int)
    statusUpdated      =QtCore.pyqtSignal(str)
    doneWithResult     =QtCore.pyqtSignal(list)
    finishedOK         =QtCore.pyqtSignal()
    finishedWithCancel =QtCore.pyqtSignal()
    finishedWithError  =QtCore.pyqtSignal(str)

    def __init__(self, args, parent=None):
        super().__init__(parent)
        self.args=args
        self._cancel_event=None

    def cancel(self):
        if self._cancel_event is not None:
            self._cancel_event.set()

    def run(self):
        try:
            seqdict1, seqiddict, hasn, minoverlap, mode, gapmode, nprocs, outroot=self.args
            if nprocs>1:
                ctx=get_mp_context()
                self._cancel_event=ctx.Event()
            else:
                self._cancel_event=None  
            md=measuredist(seqdict1, mode, gapmode, minoverlap, seqiddict, outroot, hasn, nprocs, self._cancel_event)
            md.notifyProgress.connect(self.progressUpdated.emit)
            md.notifyStatus.connect(self.statusUpdated.emit)   
            md.taskFinished.connect(self.doneWithResult.emit)
            md.run()

            self.finishedOK.emit()

        except SystemExit as e:
            if str(e)=="__CANCELLED__":
                self.finishedWithCancel.emit()
            else:
                tb=traceback.format_exc()
                sys.stderr.write(f"\n[ERROR] Exception in DistanceStarter.run:\n{tb}\n")
                sys.stderr.flush()
                self.finishedWithError.emit(f"{type(e).__name__}: {e}")

        except Exception as e:
            tb=traceback.format_exc()
            sys.stderr.write(f"\n[ERROR] Exception in DistanceStarter.run:\n{tb}\n")
            sys.stderr.flush()
            self.finishedWithError.emit(f"{type(e).__name__}: {e}")

class QtLogHandler(logging.Handler):
    def __init__(self, signal):
        super().__init__()
        self.signal=signal
    def emit(self, record):
        msg=self.format(record)
        self.signal.emit(msg)     

def _find_executable(name: str)->str:
    path=resource_path(name)
    if os.path.isfile(path):
        return path
    if platform.system()=="Windows" and os.path.isfile(path+".exe"):
        return path+".exe"
    raise FileNotFoundError(f"Required executable '{name}' not found at {path}")

class CancelableMsgBox(QtWidgets.QMessageBox):
    def __init__(self, parent=None, on_cancel=None):
        super().__init__(QtWidgets.QMessageBox.Information,
                         "Progress",
                         'Preparing workers',
                         QtWidgets.QMessageBox.NoButton,
                         parent)
        self._on_cancel=on_cancel
        self._cancel_clicked=False

    def trigger_cancel(self):
        self._cancel_clicked=True
        if callable(self._on_cancel):
            self._on_cancel()

def pair_task(args):
    seq, remseq, mode, gapmode, minoverlap, hasN, seqdict1, seqiddict=args
    if mode=='hom':
        dist=bsm.measurepair_distancehom(seq, remseq, hasN[seq], hasN[remseq], minoverlap)
    else:
        dist=bsm.measurepair_distancem_fastwrapper(seq, remseq, minoverlap)
    if dist is False:
        ids1=[seqiddict[x] for x in seqdict1[seq]]
        ids2=[seqiddict[x] for x in seqdict1[remseq]]
        return None, (ids1, ids2)
    return dist, (seq, remseq)

class BlastRunner(QtCore.QThread):
    notifyLine=QtCore.pyqtSignal(str)
    taskFinished=QtCore.pyqtSignal(int, str)

    def __init__(self, query_fa, db_fa, opts, parent=None):
        super().__init__(parent)
        self.query_fa=query_fa
        self.db_fa=db_fa
        self.opts=opts
        self._proc=None

    def cancel(self):
        if self._proc and self._proc.poll() is None:
            try:
                if platform.system()=="Windows":
                    self._proc.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    os.killpg(os.getpgid(self._proc.pid), signal.SIGTERM)
                self._proc.wait(timeout=15)
            except Exception:
                try:
                    self._proc.terminate()
                    self._proc.wait(timeout=5)
                except Exception:
                    try:
                        self._proc.kill()
                    except Exception:
                        pass

    def run(self):
        outprefix=self.opts["outprefix"]
        dbpath=outprefix+"_db"
        blastout=outprefix+".tsv"
        finalfa=outprefix+".final.fa"
        qclean=outprefix+".query.cleaned.fa"
        seen={}
        with open(self.query_fa) as fh:
            seqid, seq=None, []
            for line in fh:
                if line.startswith(">"):
                    if seqid:
                        clean="".join(seq).replace("-", "").replace("?", "").upper()
                        clean=normalize_sequence(clean)
                        if clean and clean not in seen:
                            seen[clean]=seqid
                    seqid=line.strip()[1:]
                    seq=[]
                else:
                    seq.append(line.strip())
            if seqid:
                clean="".join(seq).replace("-", "").replace("?", "").upper()
                clean=normalize_sequence(clean)
                if clean and clean not in seen:
                    seen[clean]=seqid

        with open(qclean, "w") as out:
            for clean, sid in seen.items():
                out.write(">"+sid+"\n")
                for i in range(0, len(clean), 80):
                    out.write(clean[i:i+80]+"\n")
        if not os.path.exists(self.db_fa):
            with open(self.db_fa, "w") as out:
                for sid, seq in self.parent.extsequences.items():
                    out.write(">"+sid+"\n")
                    for i in range(0, len(seq), 80):
                        out.write(seq[i:i+80]+"\n")

        cmd1=[_find_executable("makeblastdb"),"-in", self.db_fa,"-dbtype", "nucl","-out", dbpath]

        self.notifyLine.emit("Running: "+" ".join(f'"{x}"' if " " in x else x for x in cmd1))

        if platform.system()=="Windows":
            self._proc=subprocess.Popen(cmd1,
                                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                          universal_newlines=True,
                                          creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            self._proc=subprocess.Popen(cmd1,
                                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                          universal_newlines=True,
                                          preexec_fn=os.setsid)

        for line in self._proc.stdout:
            self.notifyLine.emit(line.rstrip("\n"))
        rc=self._proc.wait()
        self._proc=None
        if rc != 0:
            self.taskFinished.emit(rc, outprefix)
            return


        cmd2=[_find_executable("blastn"),
                "-query", qclean,
                "-db", dbpath,
                "-num_threads", str(self.opts["threads"]),
                "-perc_identity", str(self.opts["identity"]),
                "-max_target_seqs", str(self.opts["maxhits"]),
                "-outfmt","6"]

        self.notifyLine.emit("Running: "+" ".join(f'"{x}"' if " " in x else x for x in cmd2))

        if platform.system()=="Windows":
            self._proc=subprocess.Popen(cmd2,
                                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                          universal_newlines=True,
                                          creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            self._proc=subprocess.Popen(cmd2,
                                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                          universal_newlines=True,
                                          preexec_fn=os.setsid)

        with open(blastout, "w") as fout:
            for line in self._proc.stdout:
                fout.write(line)
                if line.startswith("Warning") or line.startswith("Error"):
                    self.notifyLine.emit(line.rstrip("\n"))
        rc=self._proc.wait()
        self._proc=None
        if rc != 0:
            self.taskFinished.emit(rc, outprefix)
            return


        if rc != 0:
            self.taskFinished.emit(rc, outprefix)
            return
        maxlen=self._get_longest_seq(self.query_fa)
        cutoff=self.opts["hitlenfrac"]*maxlen
        keep_ranges={}   
        sid_map={}
        with open(self.db_fa) as fh:
            for line in fh:
                if line.startswith(">"):
                    full=line.strip()[1:]
                    token=full.split()[0]
                    sid_map[token]=full

        with open(blastout) as fh:
            for line in fh:
                toks=line.strip().split("\t")
                if len(toks)<11:
                    continue
                token=toks[1].split()[0]
                fullid=sid_map.get(token)
                if not fullid:
                    continue
                hitlen=int(toks[3])
                sstart=int(toks[8])
                send  =int(toks[9])
                if hitlen >= cutoff:
                    keep_ranges.setdefault(fullid, []).append((sstart, send))

        merged={}
        for sid, spans in keep_ranges.items():
            minpos=min(min(s, e) for (s, e) in spans)
            maxpos=max(max(s, e) for (s, e) in spans)
            strand_votes=[("+" if s <= e else "-") for (s, e) in spans]
            strand=max(set(strand_votes), key=strand_votes.count)
            merged[sid]=(minpos, maxpos, strand)

        self._extract_merged(self.db_fa, merged, finalfa)
        self.taskFinished.emit(0, outprefix)

    def _get_longest_seq(self, fasta):
        maxlen=0
        seq=""
        with open(fasta) as fh:
            for line in fh:
                if line.startswith(">"):
                    if seq:
                        maxlen=max(maxlen, len(seq))
                        seq=""
                else:
                    seq+=line.strip()
            if seq:
                maxlen=max(maxlen, len(seq))
        return maxlen

    def _extract_merged(self, fasta, merged, outfile):
        def revcomp(seq):
            table=str.maketrans("ACGTRYMKSWBDHVNacgtrymkswvhdbn",
                                  "TGCAYRKMSWVHDBNtgcayrkmswvhdbn")
            return seq.translate(table)[::-1]

        tsvfile=outfile+".tsv"
        with open(outfile, "w") as out, open(tsvfile, "w") as meta, open(fasta) as fh:
            meta.write("id\tstrand\tstart\tend\n")
            seqid, seq=None, []
            for line in fh:
                if line.startswith(">"):
                    if seqid and seqid in merged:
                        fullseq="".join(seq)
                        s, e, _=merged[seqid]
                        if s <= e:
                            subseq=fullseq[s-1:e]
                            strand="+"
                            start0, end0=s, e
                        else:
                            subseq=revcomp(fullseq[e-1:s])
                            strand="-"
                            start0, end0=e, s
                        out.write(">"+seqid+"\n")
                        for i in range(0, len(subseq), 80):
                            out.write(subseq[i:i+80]+"\n")
                        meta.write(f"{seqid}\t{strand}\t{start0}\t{end0}\n")
                    seqid=line.strip()[1:]
                    seq=[]
                else:
                    seq.append(line.strip())
            if seqid and seqid in merged:
                fullseq="".join(seq)
                s, e, _=merged[seqid]
                if s <= e:
                    subseq=fullseq[s-1:e]
                    strand="+"
                    start0, end0=s, e
                else:
                    subseq=revcomp(fullseq[e-1:s])
                    strand="-"
                    start0, end0=e, s
                out.write(">"+seqid+"\n")
                for i in range(0, len(subseq), 80):
                    out.write(subseq[i:i+80]+"\n")
                meta.write(f"{seqid}\t{strand}\t{start0}\t{end0}\n")

class BlastSettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, indir="", fasta_path="", default_prefix=""):
        super().__init__(parent)
        self.setWindowTitle("Settings: BLAST search")
        self.setModal(True)
        form=QtWidgets.QFormLayout(self)

        self.indir=indir
        self.fasta_path=fasta_path

        self.outprefix=QtWidgets.QLineEdit(os.path.join(indir, default_prefix))
        browse=QtWidgets.QPushButton("Browse…")
        hb=QtWidgets.QHBoxLayout()
        hb.addWidget(self.outprefix); hb.addWidget(browse)
        form.addRow("Output prefix (-o)", hb)
        browse.clicked.connect(self._browse_outprefix)

        def dbl(default, lo=0.0, hi=100.0, step=0.1, dec=2):
            w=QtWidgets.QDoubleSpinBox()
            w.setRange(lo, hi)
            w.setDecimals(dec)
            w.setSingleStep(step)
            w.setValue(default)
            return w

        def intr(default, lo=1, hi=1000, step=1):
            w=QtWidgets.QSpinBox()
            w.setRange(lo, hi)
            w.setSingleStep(step)
            w.setValue(default)
            return w

        self.threads=intr(4, 1, 128)
        self.identity=dbl(95.0, 0.0, 100.0, 0.5, 2)
        self.hitlenfrac=dbl(0.75, 0.0, 1.0, 0.05, 3)
        self.maxhits=intr(100, 1, 10000)

        form.addRow("Threads", self.threads)
        form.addRow("Identity cutoff (%)", self.identity)
        form.addRow("Hit length cutoff (fraction)", self.hitlenfrac)
        form.addRow("Number of hits", self.maxhits)

        btns=QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok|QtWidgets.QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def _browse_outprefix(self):
        d=QtWidgets.QFileDialog.getExistingDirectory(self, "Choose output folder", self.indir or "")
        if d:
            stem=os.path.basename(self.outprefix.text()) or "out"
            self.outprefix.setText(os.path.join(d, stem))

    def params(self):
        return {
            "outprefix": self.outprefix.text().strip(),
            "threads": self.threads.value(),
            "identity": self.identity.value(),
            "hitlenfrac": self.hitlenfrac.value(),
            "maxhits": self.maxhits.value(),
        }

def simpifyambs(seq):
    trans=str.maketrans({"R":"N","Y":"N","M":"N","K":"N","S":"N","W":"N","B": "N", "D": "N","H": "N", "V": "N"})
    return seq.translate(trans)
def _count_fasta_records(path: str) -> int:
    n=0
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if line.startswith(">"):
                n+=1
    return n

def _mk_run_root(infile=None):
    ts=datetime.datetime.fromtimestamp(int(time.time())).strftime("%Y%m%d_%H%M%S")
    if infile:
        base_dir=os.path.dirname(os.path.abspath(infile))
    else:
        base_dir=os.getcwd()
    runroot=os.path.join(base_dir, f"IntegraTaxOut_{ts}")
    os.makedirs(runroot, exist_ok=True)
    return runroot

class HomologyJobDialog(QtWidgets.QDialog):
    cancelRequested=QtCore.pyqtSignal()
    proceedRequested=QtCore.pyqtSignal()  
    finishRequested=QtCore.pyqtSignal() 

    def __init__(self, parent=None, title="Homology search", subtitle="Finding homologous windows…"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(False)
        self.setMinimumSize(800, 500) 
        self.resize(900, 600) 



        titleLbl=QtWidgets.QLabel(title)
        titleLbl.setStyleSheet("font-size: 17px; font-weight: 600; margin-bottom:4px;")
        self.subLbl=QtWidgets.QLabel(subtitle)
        self.subLbl.setStyleSheet("color:#666;")

        self.progress=QtWidgets.QProgressBar()
        self.progress.setRange(0, 0) 
        self.toggleBtn=QtWidgets.QToolButton()
        self.toggleBtn.setText("Show details ▾")
        self.toggleBtn.setCheckable(True)
        self.toggleBtn.setChecked(False)
        self.toggleBtn.setStyleSheet("QToolButton { color:#555; }")
        self.toggleBtn.toggled.connect(self._toggleDetails)

        self.log=QtWidgets.QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setLineWrapMode(QtWidgets.QPlainTextEdit.WidgetWidth)
        self.log.setVisible(False)
        self.log.setStyleSheet(
            "QPlainTextEdit { background:#fafafa; border:1px solid #e5e5e5; border-radius:8px; padding:8px; }"
        )

        self.cancelBtn=QtWidgets.QPushButton("Cancel")
        self.cancelBtn.clicked.connect(self.cancelRequested.emit)
        self.saveBtn=QtWidgets.QPushButton("Save log…")
        self.saveBtn.clicked.connect(self._saveLog)

        self.btnRow=QtWidgets.QHBoxLayout()
        self.btnRow.addWidget(self.toggleBtn)
        self.btnRow.addStretch(1)
        self.btnRow.addWidget(self.saveBtn)
        self.btnRow.addWidget(self.cancelBtn)

        self.summaryCard=QtWidgets.QFrame()
        self.summaryCard.setVisible(False)
        self.summaryCard.setStyleSheet(
            "QFrame { background:#fff; border:1px solid #eaeaea; border-radius:10px; }"
        )
        sLay=QtWidgets.QVBoxLayout(self.summaryCard)
        sLay.setContentsMargins(12, 12, 12, 12)
        sLay.setSpacing(6)
        sTitle=QtWidgets.QLabel("Homology summary")
        sTitle.setStyleSheet("font-weight:600;")
        self.summaryLbl=QtWidgets.QLabel("")  
        self.summaryLbl.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        sLay.addWidget(sTitle)
        sLay.addWidget(self.summaryLbl)

        self.proceedBtn=QtWidgets.QPushButton("Proceed to the next step")
        self.finishBtn =QtWidgets.QPushButton("Finish here")
        self.proceedBtn.clicked.connect(self.proceedRequested.emit)
        self.finishBtn.clicked.connect(self.finishRequested.emit)
        self.proceedBtn.setVisible(False)
        self.finishBtn.setVisible(False)

        finalRow=QtWidgets.QHBoxLayout()
        finalRow.addStretch(1)
        finalRow.addWidget(self.finishBtn)
        finalRow.addWidget(self.proceedBtn)

        card=QtWidgets.QFrame()
        card.setStyleSheet("QFrame { background:#fff; border:1px solid #eaeaea; border-radius:12px; }")
        inner=QtWidgets.QVBoxLayout(card)
        inner.setContentsMargins(16,16,16,16)
        inner.setSpacing(10)
        inner.addWidget(titleLbl)
        inner.addWidget(self.subLbl)
        inner.addWidget(self.progress)
        inner.addLayout(self.btnRow)
        inner.addWidget(self.log)
        inner.addWidget(self.summaryCard)
        inner.addLayout(finalRow)

        root=QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(8,8,8,8)
        root.addWidget(card)

        self._outdir=None
        self.log.setMinimumHeight(250)    
        self.summaryCard.setMinimumHeight(100)
    def closeEvent(self, event):
        parent=self.parent()
        try:
            running=hasattr(parent, "hrunner") and parent.hrunner.isRunning()
        except Exception:
            running=False
        if running:
            self.cancelRequested.emit()
            try:
                self.setSubtitle("Cancelling… Please wait")
                self.progress.setRange(0, 0) 
            except Exception:
                pass
            event.ignore() 
            return
        event.accept()

    def setOutdir(self, outdir: str):
        self._outdir=outdir

    def setSubtitle(self, text: str):
        self.subLbl.setText(text)

    def appendLine(self, line: str):
        if not self.log.isVisible():
            self.toggleBtn.setText("Show details ▾ (logging…)")
        self.log.appendPlainText(line)

    def showSummary(self, summary_text: str):

        self.progress.setRange(0, 1)
        self.progress.setValue(1)

        self.summaryLbl.setText(summary_text)
        self.summaryCard.setVisible(True)
        self.cancelBtn.setVisible(False)
        self.proceedBtn.setVisible(True)
        self.finishBtn.setVisible(True)
        if self.height()<500:
            self.resize(self.width(), 500)
    def _toggleDetails(self, checked: bool):
        self.log.setVisible(checked)
        self.toggleBtn.setText("Hide details ▴" if checked else "Show details ▾")
        if checked and self.height()<420:
            self.resize(self.width(), 420)

    def _saveLog(self):
        fn, _=QtWidgets.QFileDialog.getSaveFileName(self, "Save log", "homology.log", "Log (*.log);;Text (*.txt)")
        if fn:
            with open(fn, "w", encoding="utf-8") as f:
                f.write(self.log.toPlainText())

class EdlibHomologyRunner(QtCore.QThread):
    notifyLine=QtCore.pyqtSignal(str)
    taskFinished=QtCore.pyqtSignal(int, str)

    def __init__(self, fasta, opts, parent=None):
        super().__init__(parent)
        self.fasta=fasta
        self.opts=opts
        self._proc=None
        self._py_tid=None
    def run(self):
        try:
            self._py_tid=threading.get_ident()
            script=resource_path("edlib_find_homology.py")
            sys_argv_backup=sys.argv[:]
            argv=[
                script,
                self.fasta,
                "-o", self.opts["outprefix"],
                "--nprop", str(self.opts["nprop"]),
                "--nsecsample", str(self.opts["nsecsample"]),
                "--minlenfrac", str(self.opts["minlenfrac"]),
                "--bw", self.opts["kde_bw"],
                "--qrange", f"{self.opts['kde_q_low']},{self.opts['kde_q_high']}",
                "--minprom", str(self.opts["kde_min_prom"]),
            ]
            if self.opts.get("thresh1") is not None:
                argv.extend(["--thresh1", str(self.opts["thresh1"])])
            if self.opts.get("thresh2") is not None:
                argv.extend(["--thresh2", str(self.opts["thresh2"])])

            sys_argv_backup=sys.argv[:]
            sys.argv=argv

            logger=logging.getLogger("edlib")
            handler=QtLogHandler(self.notifyLine)
            handler.setFormatter(logging.Formatter("%(message)s"))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

            runpy.run_path(script, run_name="__main__")
            rc=0

        except SystemExit as e:
            rc=e.code if isinstance(e.code, int) else 1
        except Exception as e:
            self.notifyLine.emit(f"[error] {e}")
            rc=1
        finally:
            sys.argv=sys_argv_backup
            try:
                logger.removeHandler(handler)
            except Exception:
                pass

        self.taskFinished.emit(rc, self.opts["outprefix"])

    def cancel(self):
        self.notifyLine.emit("Cancellation requested…")
        try:
            if self.isRunning():
                if not self._raise_async_exception(SystemExit):
                    self.terminate()
        except Exception as e:
            self.notifyLine.emit(f"[cancel] {e}")

    def _raise_async_exception(self, exctype):
        import ctypes
        tid=getattr(self, "_py_tid", None)
        if not tid:
            return False
        res=ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(tid),
            ctypes.py_object(exctype)
        )
        if res==0:
            return False
        elif res>1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), 0)
            return False
        return True

class HomologySettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, indir="", fasta_path="", default_prefix=""):
        super().__init__(parent)
        self.setWindowTitle("Settings · Homology search")
        self.setModal(True)
        form=QtWidgets.QFormLayout(self)

        self.indir=indir
        self.fasta_path=fasta_path

        self.outprefix=QtWidgets.QLineEdit(os.path.join(indir, default_prefix))
        browse=QtWidgets.QPushButton("Browse…")
        hb=QtWidgets.QHBoxLayout()
        hb.addWidget(self.outprefix); hb.addWidget(browse)
        form.addRow("Output prefix", hb)
        browse.clicked.connect(self._browse_outprefix)

        def dbl(default, lo=0.0, hi=1.0, step=0.01, dec=4):
            w=QtWidgets.QDoubleSpinBox(); w.setRange(lo,hi); w.setDecimals(dec); w.setSingleStep(step); w.setValue(default); return w
        def intr(default, lo=1, hi=1000000, step=1):
            w=QtWidgets.QSpinBox(); w.setRange(lo,hi); w.setSingleStep(step); w.setValue(default); return w

        self.nprop=dbl(0.01)
        self.nsecsample=intr(10, 1, 10000)
        self.minlen=dbl(0.75)
        self.fthresh1=dbl(0.0)
        self.fthresh1.setSpecialValueText("None")
        self.fthresh2=dbl(0.0)
        self.fthresh2.setSpecialValueText("None")

        self.kde_bw=QtWidgets.QComboBox()
        self.kde_bw.addItems(["silverman", "scott"])
        self.kde_q_low=dbl(0.001, 0.0, 1.0, 0.001, 4)
        self.kde_q_high=dbl(0.999, 0.0, 1.0, 0.001, 4)
        self.kde_minprom=dbl(0.05, 0.0, 1.0, 0.01, 3)

        form.addRow("Max proportion of N", self.nprop)
        form.addRow("Number of sequences for 2nd pass", self.nsecsample)
        form.addRow("Min length fraction", self.minlen)
        form.addRow("Bandwidth", self.kde_bw)
        form.addRow("KDE q_low", self.kde_q_low)
        form.addRow("KDE q_high", self.kde_q_high)
        form.addRow("Min prominence", self.kde_minprom)
        form.addRow("Fixed threshold pass 1", self.fthresh1)
        form.addRow("Fixed threshold pass 2", self.fthresh2)



        btns=QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        form.addRow(btns)

    def _browse_outprefix(self):
        d=QtWidgets.QFileDialog.getExistingDirectory(self, "Choose output folder", self.indir or "")
        if d:
            stem=os.path.basename(self.outprefix.text()) or "out"
            self.outprefix.setText(os.path.join(d, stem))

    def params(self):
        def opt_from_spin(spinbox):
            if spinbox.specialValueText() and spinbox.value()==spinbox.minimum():
                return None
            return spinbox.value()
        return {
            "outprefix": self.outprefix.text().strip(),
            "nprop": self.nprop.value(),
            "nsecsample": self.nsecsample.value(),
            "minlenfrac": self.minlen.value(),
            "kde_bw": self.kde_bw.currentText(),
            "kde_q_low": self.kde_q_low.value(),
            "kde_q_high": self.kde_q_high.value(),
            "kde_min_prom": self.kde_minprom.value(),
            "thresh1": opt_from_spin(self.fthresh1),
            "thresh2": opt_from_spin(self.fthresh2),
        }
   #     if p["fixed_threshold"]=="": p["fixed_threshold"]=None
   #     if p["pass2_fixed_threshold"]=="": p["pass2_fixed_threshold"]=None
     #   return p
def get_mp_context():

    if getattr(sys, "frozen", False) or sys.platform.startswith("win"):
        return mp.get_context("spawn")
    try:
        return mp.get_context("spawn")
    except ValueError:
        return mp.get_context("spawn")

def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path=getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        if platform.system()=="Darwin":
            contents_dir=os.path.abspath(os.path.join(base_path, ".."))
            possible_res=os.path.join(contents_dir, "Resources")
            if os.path.isdir(possible_res):
                base_path=possible_res
            else:
                base_path=os.path.join(base_path, "Resources")
        else:
            base_path=os.path.join(base_path, "Resources")

    else:
        base_path=os.path.join(os.path.abspath(os.path.dirname(__file__)), "Resources")

    return os.path.join(base_path, relative_path)

class PairTableDialog(QtWidgets.QDialog):
    def __init__(self, pair_list, parent=None):
        super(PairTableDialog, self).__init__(parent)
        self.setWindowTitle("These pairs do not meet the overlaplength requirement")
        self.setMinimumSize(300, 300)

        layout=QtWidgets.QVBoxLayout(self)

        self.table=QtWidgets.QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Item 1", "Item 2"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)

        self.populate_table(pair_list)

        layout.addWidget(self.table)

        button_box=QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def populate_table(self, pair_list):
        self.table.setRowCount(len(pair_list))
        for row_idx, (item1, item2) in enumerate(pair_list):
            self.table.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(str(item1)))
            self.table.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(str(item2)))

class PicButton(QtWidgets.QAbstractButton):
    def __init__(self, pixmap, pixmap_hover, pixmap_pressed, parent=None):
        super(PicButton, self).__init__(parent)
        self.setCheckable(True)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.setMouseTracking(True)
        self.toggled.connect(self.setcheckedbtn)
        self.pixmap=pixmap
        self.pixmap_hover=pixmap_hover
        self.pixmap_pressed=pixmap_pressed
        self.toggled.connect(self.setcheckedbtn)
      #   self.released.connect(self.update)

    def paintEvent(self, event):
        if self.isChecked():
            pix=self.pixmap_pressed
        elif self.underMouse():
            pix=self.pixmap_hover
        else:
            pix=self.pixmap

        painter=QtGui.QPainter(self)
        painter.drawPixmap(self.rect(), pix)

    def enterEvent(self, event):
        self.update()

    def leaveEvent(self, event):
        self.update()
    def setcheckedbtn(self):
        
        self.update()

    def sizeHint(self):
        return QtCore.QSize(100, 100)
seqdict1_g=None
seqiddict_g=None
hasn_g=None
minoverlap_g=None
mode_g=None
gapmode_g=None
def run_measuredist_process(args, queue, cancel_event):
    seqdict1, seqiddict, hasn, minoverlap, mode, gapmode, nprocs, outroot=args
    md=measuredist(seqdict1, mode, gapmode, minoverlap, seqiddict, outroot, hasn, nprocs, cancel_event)

    def forward_progress(pct):
        queue.put(("progress", pct))
    def forward_finish(res):
        queue.put(("done", res))

    md.notifyProgress.connect(forward_progress)
    md.taskFinished.connect(forward_finish)
    try:
        md.run()
    except SystemExit as e:
        if str(e)=="__CANCELLED__":
            try:
                queue.put(("cancelled", None))
            except Exception:
                pass
        else:
            try:
                queue.put(("error", f"SystemExit: {e}"))
            except Exception:
                pass
    except Exception as e:
        try:
            queue.put(("error", f"{type(e).__name__}: {e}"))
        except Exception:
            pass

progress_value_g=None
progress_lock_g =None
write_queue_g   =None

def file_writer_single(q, pdistdir, lru_cap=256):

    from collections import OrderedDict
    open_fhs=OrderedDict()
    try:
        while True:
            item=q.get()
            if item is None:
                break
            bin_key, lines=item
            if not lines:
                continue

            fh=open_fhs.pop(bin_key, None)
            if fh is None:
                if len(open_fhs) >= lru_cap:
                    old_key, old_fh=open_fhs.popitem(last=False)
                    try: old_fh.close()
                    except Exception: pass
                path=os.path.join(pdistdir, bin_key)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                fh=open(path, "a", buffering=1024*1024)
            open_fhs[bin_key]=fh  
            fh.writelines(lines)
    except Exception:
        import traceback
        print("[writer_single] crashed:\n", traceback.format_exc(), flush=True)
    finally:
        for _, fh in list(open_fhs.items()):
            try: fh.close()
            except Exception: pass
        open_fhs.clear()


def init_worker_globals(seqdict1_, seqiddict_, hasn_, minoverlap_, mode_, gapmode_, pdistdir_, cancel_flag_):
    global seqdict1_g, seqiddict_g, hasn_g, minoverlap_g, mode_g, gapmode_g, pdistdir_g, cancel_flag_g
    seqdict1_g, seqiddict_g, hasn_g=seqdict1_, seqiddict_, hasn_
    minoverlap_g, mode_g, gapmode_g, pdistdir_g=minoverlap_, mode_, gapmode_, pdistdir_
    cancel_flag_g=cancel_flag_



def _compute_batch_singlecore(batch, seqdict1, seqiddict, hasn, minoverlap, mode, pdistdir,
                              progress_value=None, progress_lock=None, write_queue=None,
                              custom_flush=None):

    pid=os.getpid()
    buffers={}
    overlap_pairs=[]
    flush_threshold=250_000
    tick, TICK_STEP=0, 4096

    def flush_bin(bin_key, buf):
        if custom_flush:
            if buf:
                custom_flush(bin_key, buf)
            return
        if not buf:
            return
        while True:
            try:
                if write_queue:
                    write_queue.put((bin_key, buf[:]), block=False)
                else:
                    path=os.path.join(pdistdir, bin_key)
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, "a") as fh:
                        fh.writelines(buf)
                buf.clear()
                break
            except queue.Full:
                time.sleep(0.02)



    for seq, remseq in batch:
        if mode=="hom":
            dist=bsm.measurepair_distancehom(seq, remseq, hasn[seq], hasn[remseq], minoverlap)
        else:
            dist=bsm.measurepair_distancem_fastwrapper(seq, remseq, minoverlap)

        tick+=1
        if progress_value is not None and tick >= TICK_STEP:
            with progress_lock:
                progress_value.value+=tick
            tick=0

        if dist is False:
            ids1=[seqiddict[x] for x in seqdict1[seq]]
            ids2=[seqiddict[x] for x in seqdict1[remseq]]
            overlap_pairs.append((ids1, ids2))
            continue

        idx=int(round(dist*10000))
        bin_key=f"{idx/100:.2f}"
        line=f"{seqdict1[seq][0]}\t{seqdict1[remseq][0]}\n"

        buf=buffers.get(bin_key)
        if buf is None:
            buf=[]
            buffers[bin_key]=buf
        buf.append(line)
        if len(buf) >= flush_threshold:
            flush_bin(bin_key, buf)

    if progress_value is not None and tick:
        with progress_lock:
            progress_value.value+=tick

    for k, buf in buffers.items():
        flush_bin(k, buf)

    if overlap_pairs:
        tmp_err=os.path.join(pdistdir, "tmp", "overlap_errors")
        os.makedirs(tmp_err, exist_ok=True)
        with open(os.path.join(tmp_err, f"w{pid}.tsv"), "a") as fh:
            for ids1, ids2 in overlap_pairs:
                fh.write(f"{ids1}\t{ids2}\n")

    return len(batch)
def _run_singlecore(self, seqdict1, seqiddict, hasn, minoverlap, mode, gapmode):
    from collections import OrderedDict

    overlaperror=[]
    total_buffered=[0]
    MAX_BUFFERED_LINES=5_000_000
    LRU_CAP=256
    open_fhs=OrderedDict()
    buffers={}
    processed=0

    def get_fh(bin_key):
        fh=open_fhs.pop(bin_key, None)
        if fh is None:
            if len(open_fhs) >= LRU_CAP:
                old_key, old_fh=open_fhs.popitem(last=False)
                try: old_fh.close()
                except Exception: pass
            path=os.path.join(self.pdistdir, bin_key)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            fh=open(path, "a", buffering=1024*1024)
        open_fhs[bin_key]=fh
        return fh

    def flush_bin(bin_key, buf):
        if not buf: return
        fh=get_fh(bin_key)
        fh.writelines(buf)
        total_buffered[0]-=len(buf)
        buf.clear()

    keys=list(seqdict1.keys())
    n=len(keys)
    total_pairs=n*(n - 1) // 2
    processed=0
    last_emit=time.time()

    def emit_progress(force=False):
        nonlocal last_emit
        now=time.time()
        if force or now - last_emit >= 1.0:
            pct=int((done_pairs / max(1, total_pairs))*100)
            self.notifyProgress.emit(min(100, max(0, pct)))

            last_emit=now

    for i, seq in enumerate(keys):
        for remseq in keys[i+1:]:
            if mode=="hom":
                dist=bsm.measurepair_distancehom(seq, remseq, hasn[seq], hasn[remseq], minoverlap)
            else:
                dist=bsm.measurepair_distancem_fastwrapper(seq, remseq, minoverlap)
            processed+=1
            if dist is False:
                ids1=[seqiddict[x] for x in seqdict1[seq]]
                ids2=[seqiddict[x] for x in seqdict1[remseq]]
                overlaperror.append((ids1, ids2))
                continue
            idx=int(round(dist*10000))
            bin_key=f"{idx/100:.2f}"
            line=f"{seqdict1[seq][0]}\t{seqdict1[remseq][0]}\n"
            buf=buffers.setdefault(bin_key, [])
            buf.append(line)
            total_buffered[0]+=1
            if len(buf) >= 250_000:
                flush_bin(bin_key, buf)
            if total_buffered[0] >= MAX_BUFFERED_LINES:
                for k, b in sorted(buffers.items(), key=lambda kv: len(kv[1]), reverse=True)[:50]:
                    flush_bin(k, b)
                    if total_buffered[0]<MAX_BUFFERED_LINES // 2:
                        break
        emit_progress()

    for key, buf in buffers.items():
        flush_bin(key, buf)
    for _, fh in open_fhs.items():
        try: fh.close()
        except Exception: pass
    self.notifyProgress.emit(100)
    self.taskFinished.emit(overlaperror)

class measuredist(QtCore.QThread):
    notifyProgress=QtCore.pyqtSignal(int)
    notifyStatus=QtCore.pyqtSignal(str)  
    taskFinished=QtCore.pyqtSignal(list)
    def __init__(self, seqdict1, mode, gapmode, minoverlap, seqiddict, outroot, hasN, nproc, cancel_event=None):
        super(measuredist, self).__init__()
        self.seqdict1=seqdict1
        self.mode=mode
        self.gapmode=gapmode
        self.minoverlap=minoverlap
        self.seqiddict=seqiddict
        self.outroot=outroot
        self.hasN_flags=hasN
        self.nprocs=nproc
        self._cancel_event=cancel_event
    def cancel(self):
        self._should_cancel=True
    def run(self):
        # --- Local aliases
        seqdict1  =self.seqdict1
        seqiddict =self.seqiddict
        hasn      =self.hasN_flags
        minoverlap=self.minoverlap
        mode      =self.mode
        gapmode   =self.gapmode
        self.pdistdir=os.path.abspath(os.path.join(self.outroot, "pmatrix"))
        streams_dir  =os.path.join(self.pdistdir, "worker_streams")
        tmp_dir      =os.path.join(self.pdistdir, "tmp")
        os.makedirs(self.pdistdir, exist_ok=True)
        os.makedirs(streams_dir,  exist_ok=True)
        os.makedirs(tmp_dir,      exist_ok=True)

        bin_labels=["{:.2f}".format(i / 100) for i in range(0, 10001)]
        with open(os.path.join(self.outroot, "bins.txt"), "w") as o:
            o.write("\n".join(bin_labels))

        keys=list(seqdict1.keys())
        n=len(keys)
        if self.nprocs==1:
            _run_singlecore(self, seqdict1, seqiddict, hasn, minoverlap, mode, gapmode)
            return
        ctx=get_mp_context()

        progress_value=ctx.Value('q', 0)
        progress_lock =ctx.Lock()
        cancel_flag=ctx.Value('i', 0)

        mgr=ctx.Manager()


        def emit_progress_time_based(force=False):
            nonlocal last_emit
            now=time.time()
            base_interval=0.8 if total_pairs >= 100_000 else 0.4
            if force or (now - last_emit >= base_interval):
                with progress_value.get_lock():
                    done=progress_value.value
                pct=min(100, int((done / max(1, total_pairs))*100))
                self.notifyProgress.emit(min(100, pct))
                last_emit=now
        if n<1500:
            batch_size=2000
        elif n<10000:
            batch_size=6000
        else:
            batch_size=10000
        TICK_STEP =4096
        DUMP_EVERY=250_000 
        batches_iter=_pair_batches(keys, batch_size)

        pool=None
        try:
            self.notifyProgress.emit(-2)
        #    self.notifyProgress.emit(0)

            ctx=get_mp_context()

            pool=ctx.Pool(
                processes=self.nprocs,
                initializer=init_worker_globals,
                initargs=(seqdict1, seqiddict, hasn, minoverlap, mode, gapmode, self.pdistdir, cancel_flag),
            )

            self.notifyProgress.emit(-1) 
            self.notifyStatus.emit("Calculating pairwise distances…")
            total_pairs=n*(n - 1) // 2
            done_pairs=0
            last_emit=time.time()

            def emit_progress(force=False):
                nonlocal last_emit, done_pairs
                now=time.time()
                base_interval=0.8 if total_pairs >= 100_000 else 0.4
                if force or (now - last_emit >= base_interval):
                    pct=int((done_pairs / max(1, total_pairs))*100)
                    self.notifyProgress.emit(min(100, max(0, pct)))
                    last_emit=now
            def submit_fn(batch):
                return pool.apply_async(
                    _worker_batch_flatstream,
                    ((batch, minoverlap, mode, self.pdistdir, TICK_STEP, DUMP_EVERY, total_pairs),),
                )

            def _on_progress(_res):
                if self._cancel_event is not None and self._cancel_event.is_set():
                    try:
                        cancel_flag.value=1
                    except Exception:
                        pass
                    raise RuntimeError("__CANCELLED__")

                inc=_res.get("total_pairs", 0) if isinstance(_res, dict) else 0
                with progress_lock:
                    progress_value.value+=inc if inc else 0
                emit_progress_time_based()
            def check_cancel():
                if self._cancel_event and self._cancel_event.is_set():
                    raise RuntimeError("__CANCELLED__")

            max_inflight=max(2, self.nprocs*2)

            try:
                _run_balanced_pool(pool, iter(batches_iter), submit_fn, _on_progress, max_inflight)
                emit_progress_time_based(force=True)
            except RuntimeError as e:
                if str(e)=="__CANCELLED__":
                    try:
                        cancel_flag.value=1
                    except Exception:
                        pass
                    try:
                        pool.terminate()
                        pool.join(timeout=10)
                    except Exception:
                        pass
                    # Inform GUI
                    self.taskFinished.emit([("CANCELLED", None)])
                    # Ensure DistanceStarter catches cancel
                    raise SystemExit("__CANCELLED__")
                else:
                    raise


            self.notifyStatus.emit("Merge: partitioning (stage 1)…")
            emit_progress(force=True); self.notifyProgress.emit(-2)
            _radix_stage1_partition_from_workers(self.pdistdir)

            self.notifyStatus.emit("Merge: splitting buckets to pmatrix (stage 2)…")
            emit_progress(force=True); self.notifyProgress.emit(-2)
            _radix_stage2_demux_to_pmatrix(self.pdistdir, lru_cap=96)



            self.notifyStatus.emit("Finalizing temporary data…")
            emit_progress(force=True)

            overlaperror=[]
            if os.path.isdir(tmp_dir):
                for fn in os.listdir(tmp_dir):
                    if fn.startswith("overlap_") and fn.endswith(".tsv"):
                        with open(os.path.join(tmp_dir, fn)) as fh:
                            for line in fh:
                                a, b=line.rstrip("\n").split("\t")
                                overlaperror.append((a, b))
                shutil.rmtree(tmp_dir, ignore_errors=True)

            self.notifyStatus.emit("Completed.")
            self.notifyProgress.emit(100)
            self.taskFinished.emit(overlaperror)
            return

        finally:
            if pool is not None:
                try:
                    if cancel_flag.value:
                        pool.terminate()
                    else:
                        pool.close()
                    pool.join(timeout=5)
                except Exception:
                    pass
                finally:
                    del pool




class OptWindow(QtWidgets.QWidget): 
    def __init__(self,parent=None):
        super(OptWindow,self).__init__(parent)
        screen=QtWidgets.QApplication.desktop().screenGeometry()
        self.setGeometry(int(screen.width()*2/3), int(screen.height()/6),int(screen.width()/3),int(screen.height()*2/3))
        self.setWindowTitle("IntegraTax")
        self.stack=QtWidgets.QStackedWidget(self)
        self.layout=QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.stack)
        self.initFileSelectionScreen()
        self.initExternalSeqScreen()
        self.initAlignmentQuestionScreen()
        self.initHomFragScreen()
        self.initOptionsScreen()
        self.initExternalSpeciesScreen()
        self.initExternalModeScreen() 
        self.initExternalOptionsScreen()    
        self.setLayout(self.layout)
        self.runroot=None
        self._prev_cwd=None
        self.show()


    def initFileSelectionScreen(self):
        file_select_widget=QtWidgets.QWidget()
        outer_layout=QtWidgets.QVBoxLayout(file_select_widget)
        outer_layout.setContentsMargins(40, 40, 40, 40)

        container=QtWidgets.QWidget()
        container.setObjectName("mainContainer")
        container.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        container_layout=QtWidgets.QVBoxLayout(container)
        container_layout.setAlignment(QtCore.Qt.AlignTop)
        container_layout.setContentsMargins(40, 40, 40, 40)

        logo_label=QtWidgets.QLabel()
        logo_path=resource_path("logos/softwarelogo.jpg")
        pixmap=QtGui.QPixmap(logo_path)
        pixmap=pixmap.scaledToWidth(180, QtCore.Qt.SmoothTransformation)
        logo_label.setPixmap(pixmap)
        logo_label.setAlignment(QtCore.Qt.AlignCenter)
        container_layout.addWidget(logo_label)

        self.label=QtWidgets.QLabel("Drag input FASTA file here", self)
        self.label.setObjectName("dragLabel")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setStyleSheet("""
            QLabel#dragLabel {
                font-size: 18px;
                font-weight: bold;
                color: #444;
                padding: 120px 20px;
                background-color: transparent;
                border: none;
            }
        """)
        self.setAcceptDrops(True)
        container_layout.addWidget(self.label)

        container.setStyleSheet("""
            QWidget#mainContainer {
                border: 2px dashed #999;
                border-radius: 12px;
                background-color: #ffffff;
            }
        """)

        outer_layout.addWidget(container)
        self.stack.addWidget(file_select_widget)

    def initExternalSeqScreen(self):
        widget=QtWidgets.QWidget()
        main_layout=QtWidgets.QVBoxLayout(widget)
        main_layout.setContentsMargins(40, 40, 40, 40)

        top_bar=QtWidgets.QHBoxLayout()
        top_bar.setContentsMargins(10, 10, 10, 0)
        top_bar.addWidget(self.makeResetButton(), alignment=Qt.AlignLeft)
        top_bar.addStretch()
        main_layout.addLayout(top_bar)

        center=QtWidgets.QVBoxLayout()
        center.setAlignment(Qt.AlignCenter)

        question=QtWidgets.QLabel("Do you have a 2nd fasta file with identified reference sequences?")
        question.setFont(QtGui.QFont("Arial", 22, QtGui.QFont.Bold))
        question.setAlignment(Qt.AlignCenter)
        center.addWidget(question)

        btn_layout=QtWidgets.QHBoxLayout()
        btn_layout.setSpacing(20)

        no_btn=QtWidgets.QPushButton("No")
        sel_btn=QtWidgets.QPushButton("Select")
        no_btn.setFixedWidth(120)
        sel_btn.setFixedWidth(120)

        btn_layout.addWidget(no_btn)
        btn_layout.addWidget(sel_btn)
        center.addLayout(btn_layout)

        main_layout.addStretch(1)
        main_layout.addLayout(center)
        main_layout.addStretch(1)

        no_btn.clicked.connect(self._external_no)
        sel_btn.clicked.connect(self._external_select)

        self.stack.addWidget(widget)
        self.external_screen_index=self.stack.indexOf(widget)

    def _external_no(self):
        self.loadseqs(self.infilename)
        self.projectcount=self.seqcounts
        if len(self.lengths)== 1:
            self.stack.setCurrentIndex(self.align_screen_index)
        else:
            self.stack.setCurrentIndex(self.homfrag_screen_index)
    def _external_select(self):
        msg=QtWidgets.QMessageBox(self)
        msg.setWindowTitle("External sequences")
        msg.setIcon(QtWidgets.QMessageBox.Warning)
        msg.setText("External sequences will only be treated as unaligned.\n\nDo you want to continue?")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok|QtWidgets.QMessageBox.Cancel)
        choice=msg.exec_()
        if choice==QtWidgets.QMessageBox.Cancel:
            self.stack.setCurrentIndex(0)
            return

        fname,_=QtWidgets.QFileDialog.getOpenFileName(self,"Select external FASTA","","All files (*)")
        if not fname:
            self.stack.setCurrentIndex(0)
            return

        self.extseqdict={}
        self.extsequences={}
        self.extseqiddict={}
        self.extspeciesmap={}
        self.extcounts=0

        extseqid=""
        extsequence=""
        flag=0
        try:
            with open(fname) as fh:
                for line in fh:
                    if line.startswith(">"):
                        if extseqid:
                            newid="ext_"+extseqid
                            seq=extsequence.replace("-","").replace("?","").upper()
                            try:
                                self.extseqdict[seq].append(str(self.extcounts))
                            except KeyError:
                                self.extseqdict[seq]=[str(self.extcounts)]
                            self.extsequences[newid]=seq
                            self.extseqiddict[str(self.extcounts)]=newid
                            self.extcounts+=1
                        extseqid=line.strip()[1:].replace('"', '').replace("'","")
                        extsequence=""
                    else:
                        try:
                            extsequence+=line.strip()
                        except:
                            QtWidgets.QMessageBox.warning(self,"Message","Invalid Fasta")
                            flag=1
                            break
                if extseqid and flag==0:
                    newid="ext_"+extseqid
                    seq=extsequence.replace("-","").replace("?","").upper()
                    try:
                        self.extseqdict[seq].append(str(self.extcounts))
                    except KeyError:
                        self.extseqdict[seq]=[str(self.extcounts)]
                    self.extsequences[newid]=seq
                    self.extseqiddict[str(self.extcounts)]=newid
                    self.extcounts+=1
        except Exception:
            QtWidgets.QMessageBox.warning(self,"Message","Invalid Fasta")
            self.stack.setCurrentIndex(0)
            return

        if flag==1:
            self.stack.setCurrentIndex(0)
            return

        self.externalinfilename=fname
        self.extbeforecount=self.extcounts 
        pattern=r"[A-Z][a-z]*[ _-][a-z][a-z]*"
        species=set()
        for extid in self.extsequences.keys():
            m=re.findall(pattern,extid)
            if m:
                self.extspeciesmap[extid]=m[0]
                species.add(m[0])
            else:
                self.extspeciesmap[extid]=None
        species=sorted(species)

        self.exttitle.setText("Loaded "+str(self.extcounts)+" external sequences")
        for i in reversed(range(self.extscrollvbox.count())):
            w=self.extscrollvbox.itemAt(i).widget()
            if w: w.deleteLater()
        self.extspecieschecks={}
        for sp in species:
            cb=QtWidgets.QCheckBox(sp)
            cb.setChecked(True)
            self.extscrollvbox.addWidget(cb)
            self.extspecieschecks[sp]=cb
        self.extscrollvbox.addStretch()
        self.extincludeundetected.setChecked(True)
        self.extselectall.setChecked(True)

        self.stack.setCurrentIndex(self.externalspeciesindex)
    def makeResetButton(self):
        btn=QtWidgets.QToolButton()
        btn.setIcon(QtGui.QIcon(resource_path("logos/reset_icon.png")))
        btn.setIconSize(QtCore.QSize(24, 24))
        btn.setStyleSheet("""
            QToolButton {
                border: none;
                color: #444;
                font-size: 12px;
            }
            QToolButton:hover {
                color: #006400;
            }
        """)
        btn.setStyleSheet("border: none;")
        btn.setToolTip("Reset to start")
        btn.clicked.connect(self.resetToStart)
        return btn

    def initExternalModeScreen(self):
        widget=QtWidgets.QWidget()
        main_layout=QtWidgets.QVBoxLayout(widget)
        main_layout.setContentsMargins(40, 40, 40, 40)
        top_bar=QtWidgets.QHBoxLayout()
        top_bar.setContentsMargins(10, 10, 10, 0)
        top_bar.addWidget(self.makeResetButton(), alignment=Qt.AlignLeft)
        top_bar.addStretch()
        main_layout.addLayout(top_bar)
        center=QtWidgets.QVBoxLayout()
        center.setAlignment(Qt.AlignCenter)

        self.extmodetitle=QtWidgets.QLabel("")
        self.extmodetitle.setFont(QtGui.QFont("Arial", 16, QtGui.QFont.Bold))
        self.extmodetitle.setAlignment(Qt.AlignCenter)
        center.addWidget(self.extmodetitle)
        center.addSpacing(20)
        self.extopt3=QtWidgets.QRadioButton("BLAST-based homology search\nRetrieve only nearby sequences to my references.")
        self.extopt3.setChecked(True)
        center.addWidget(self.extopt3)
        center.addSpacing(25)
        self.otheroptionsbtn=QtWidgets.QPushButton("Other options ▾")
        self.otheroptionsbtn.setCheckable(True)
        self.otheroptionsbtn.setChecked(False)
        center.addWidget(self.otheroptionsbtn)
        self.otheroptionsframe=QtWidgets.QFrame()
        self.otheroptionsframe.setVisible(False)
        self.otheroptionsframe.setStyleSheet("""QFrame { background:#fff8f8; border:1px solid #f0d0d0; border-radius:8px;padding:10px;} """)
        vbox=QtWidgets.QVBoxLayout(self.otheroptionsframe)
        warn=QtWidgets.QLabel( "<b>Warning:</b> Avoid using these if your external dataset is large.<br>""This software computes all pairwise distances exhaustively.")
        warn.setStyleSheet("color: red; font-size: 11pt;")
        warn.setWordWrap(True)
        vbox.addWidget(warn)
        vbox.addSpacing(10)
        self.extopt1=QtWidgets.QRadioButton("Assume homology with my sequences.\nUse this only if confident.")
        self.extopt2=QtWidgets.QRadioButton("Find homology exhaustively.\nUse only for smaller external datasets; tries to retain all sequences.")
        vbox.addWidget(self.extopt1)
        vbox.addSpacing(10)
        vbox.addWidget(self.extopt2)
        center.addWidget(self.otheroptionsframe)
        self.modeGroup=QtWidgets.QButtonGroup(widget)
        self.modeGroup.addButton(self.extopt1)
        self.modeGroup.addButton(self.extopt2)
        self.modeGroup.addButton(self.extopt3)
        self.otheroptionsbtn.toggled.connect(self.otheroptionsframe.setVisible)
        def onotheroptionstoggled(checked):
            if checked:
                self.extopt3.setChecked(False)
            else:
                if not (self.extopt1.isChecked() or self.extopt2.isChecked()):
                    self.extopt3.setChecked(True)
        self.otheroptionsbtn.toggled.connect(onotheroptionstoggled)

        def onmodechanged(button):
            if button in (self.extopt1, self.extopt2):
                if not self.otheroptionsbtn.isChecked():
                    self.otheroptionsbtn.setChecked(True)
            elif button==self.extopt3:
                self.otheroptionsbtn.setChecked(False)
        self.modeGroup.buttonClicked.connect(onmodechanged)
        center.addSpacing(25)
        proceedbtn=QtWidgets.QPushButton("Proceed")
        proceedbtn.clicked.connect(self.finishExternalMode)
        center.addWidget(proceedbtn, alignment=Qt.AlignCenter)

        main_layout.addStretch(1)
        main_layout.addLayout(center)
        main_layout.addStretch(1)

        self.stack.addWidget(widget)
        self.externalmodeindex=self.stack.indexOf(widget)



    def finishExternalMode(self):
        if self.extopt1.isChecked():
            self.exthomologymode=1
            self.runExternalHomologyAssume()
        elif self.extopt2.isChecked():
            self.exthomologymode=2
            extfile=self.writeExternalSubset()
            self._hom_input_fasta=extfile
            self._hom_input_count=self.extcounts
            self.openhomologysettings()
        else:
            self.exthomologymode=3
            if not self.runroot:
                self.runroot=_mk_run_root(self.infilename)
            self._blast_db=os.path.join(self.runroot, "external.filtered.fa")
            self._blast_query=self.infilename
            self.openblastsettings()
        print("External homology mode selected:", self.exthomologymode)


    def initAlignmentQuestionScreen(self):
        widget=QtWidgets.QWidget()
        main_layout=QtWidgets.QVBoxLayout(widget)
        main_layout.setContentsMargins(40, 40, 40, 40)

        top_bar=QtWidgets.QHBoxLayout()
        top_bar.setContentsMargins(10, 10, 10, 0)
        top_bar.addWidget(self.makeResetButton(), alignment=Qt.AlignLeft)
        top_bar.addStretch()
        main_layout.addLayout(top_bar)

        center=QtWidgets.QVBoxLayout()
        center.setAlignment(Qt.AlignCenter)

        self.align_question=QtWidgets.QLabel(
            "I detect sequences of the same length.\n"
            "Proceed as aligned?\n"
            "If 'No' is selected, pairwise alignments will be conducted."
        )
        self.align_question.setFont(QtGui.QFont("Arial", 18, QtGui.QFont.Bold))
        self.align_question.setAlignment(Qt.AlignCenter)
        center.addWidget(self.align_question)

        btn_layout=QtWidgets.QHBoxLayout()
        btn_layout.setSpacing(20)

        yes_btn=QtWidgets.QPushButton("Yes (Aligned)")
        no_btn =QtWidgets.QPushButton("No (Pairwise)")
        yes_btn.setFixedWidth(150)
        no_btn.setFixedWidth(150)

        btn_layout.addWidget(yes_btn)
        btn_layout.addWidget(no_btn)
        center.addLayout(btn_layout)

        main_layout.addStretch(1)
        main_layout.addLayout(center)
        main_layout.addStretch(1)

        yes_btn.clicked.connect(self._align_yes)
        no_btn.clicked.connect(self._align_no)

        self.stack.addWidget(widget)
        self.align_screen_index=self.stack.indexOf(widget)


    def _align_yes(self):
        self.mode="aligned"
        self.GapGroup.setVisible(False)
        self.stack.setCurrentIndex(self.opt_screen_index)  

    def _align_no(self):
        self.stack.setCurrentIndex(self.homfrag_screen_index) 
    def initHomFragScreen(self):
        widget=QtWidgets.QWidget()
        layout=QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setAlignment(Qt.AlignCenter)
        widget.setStyleSheet("background-color: white;")
        top_bar=QtWidgets.QHBoxLayout()
        top_bar.setContentsMargins(10, 10, 10, 0)
        top_bar.addWidget(self.makeResetButton(), alignment=Qt.AlignLeft)
        top_bar.addStretch()
        layout.addLayout(top_bar)

        question=QtWidgets.QLabel("Select mode for pairwise alignment")
        question.setFont(QtGui.QFont("Arial", 20, QtGui.QFont.Bold))
        question.setAlignment(Qt.AlignCenter)
        layout.addWidget(question)
        layout.addSpacing(40)

        hom_row=QtWidgets.QHBoxLayout()
        hom_row.setAlignment(Qt.AlignCenter)

        hom_pix= QtGui.QPixmap(resource_path("logos/hom_un_unclicked.png"))
        hom_hover= QtGui.QPixmap(resource_path("logos/hom_un_hover.png"))
        hom_clicked= QtGui.QPixmap(resource_path("logos/hom_un_clicked.png"))
        self.hom_btn= PicButton(hom_pix, hom_hover, hom_clicked)
        self.hom_btn.setFixedSize(220, 220)
        self.hom_btn.clicked.connect(lambda: self.homsearchparamgo("hom"))

        hom_row.addWidget(self.hom_btn)

        hom_text=QtWidgets.QLabel("This will directly proceed to pairwise alignments.")
        hom_text.setStyleSheet("color: #666; font-size: 13px;")
        hom_text.setWordWrap(True)
        hom_text.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        hom_text.setFixedWidth(260)

        hom_row.addSpacing(30)
        hom_row.addWidget(hom_text)
        layout.addLayout(hom_row)

        layout.addSpacing(60)

        frag_row=QtWidgets.QHBoxLayout()
        frag_row.setAlignment(Qt.AlignCenter)

        frag_pix=QtGui.QPixmap(resource_path("logos/frag_un_unclicked.png"))
        frag_hover=QtGui.QPixmap(resource_path("logos/frag_un_hover.png"))
        frag_clicked=QtGui.QPixmap(resource_path("logos/frag_un_clicked.png"))
        self.frag_btn= PicButton(frag_pix, frag_hover, frag_clicked)
        self.frag_btn.setFixedSize(220, 220)
        self.frag_btn.clicked.connect(lambda: self.homsearchparamgo("frag"))

        frag_row.addWidget(self.frag_btn)

        frag_text=QtWidgets.QLabel(
            "Ensure the first sequence represents the target region.\n\n"
            "This will first trim the sequences and/or discard sequences not detected as homologous."
        )
        frag_text.setStyleSheet("color: #666; font-size: 13px;")
        frag_text.setWordWrap(True)
        frag_text.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        frag_text.setFixedWidth(260)

        frag_row.addSpacing(30)
        frag_row.addWidget(frag_text)
        layout.addLayout(frag_row)

        self.stack.addWidget(widget)
        self.homfrag_screen_index=self.stack.indexOf(widget)


    def homsearchparamgo(self, mode):
        self.mode=mode
        if mode=="frag":
            self._hom_input_fasta=self.infilename
            self._hom_input_count=_count_fasta_records(self.infilename)
            self.openhomologysettings()
        else:
            self.GapGroup.setVisible(True) 
            self.updaterunbuttonformodes()
            self.stack.setCurrentIndex(self.opt_screen_index)  
    def initOptionsScreen(self):
        options_widget=QtWidgets.QWidget()
        main_layout=QtWidgets.QVBoxLayout(options_widget)
        main_layout.setContentsMargins(40, 40, 40, 40)  
        ProcLayout=QtWidgets.QHBoxLayout()
        self.ProcLabel=QtWidgets.QLabel("Number of processors:")
        self.ProcLabel.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))

        self.ProcCombo=QtWidgets.QComboBox()
        max_procs=mp.cpu_count()
        default_procs=min(4, max_procs)  
        for i in range(1, max_procs+1):
            self.ProcCombo.addItem(str(i))
        self.ProcCombo.setCurrentText(str(default_procs))
        self.ProcCombo.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                             QtWidgets.QSizePolicy.Fixed)

        ProcLayout.addWidget(self.ProcLabel)
        ProcLayout.addWidget(self.ProcCombo)
        ProcLayout.addStretch()
        top_layout=QtWidgets.QHBoxLayout()
        self.reset_button=self.makeResetButton()

        self.loaded_label=QtWidgets.QLabel("")
        self.loaded_label.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
        self.loaded_label.setAlignment(Qt.AlignCenter)

        top_layout.addWidget(self.reset_button, alignment=Qt.AlignLeft)
        top_layout.addStretch()
        top_layout.addWidget(self.loaded_label, alignment=Qt.AlignCenter)
        top_layout.addStretch()
        
        main_layout.addLayout(top_layout)

        center_layout=QtWidgets.QVBoxLayout()
        center_layout.setAlignment(Qt.AlignCenter)

        MinOverlapLayout=QtWidgets.QHBoxLayout()
        self.MinOverlapLabel=QtWidgets.QLabel("Minimum Overlap:")
        self.MinOverlapLabel.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
        self.MinOverlapTextBox=QtWidgets.QLineEdit("100")
        self.MinOverlapTextBox.setFixedWidth(80)
   #     self.MinOverlapTextBox.textEdited.connect(self.setoverlaplen)
        self.overlaplen=100 
        self.hasN_flags={} 
        MinOverlapLayout.addWidget(self.MinOverlapLabel)
        MinOverlapLayout.addWidget(self.MinOverlapTextBox)
        MinOverlapLayout.addStretch()
        center_layout.addLayout(MinOverlapLayout)
        center_layout.addSpacing(12)
        center_layout.addLayout(ProcLayout)
        center_layout.addSpacing(12)
        species_layout=QtWidgets.QHBoxLayout()
        self.species_label=QtWidgets.QLabel("Species Names:")
        self.species_label.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
        self.DetectButton=QtWidgets.QRadioButton("Detect")
        self.DetectButton.setChecked(True)  
        self.DonotdetectButton=QtWidgets.QRadioButton("Do not detect")
        self.AssociateSpButton=QtWidgets.QRadioButton("Add species names by file")

        species_layout.addWidget(self.species_label)
        species_layout.addWidget(self.DetectButton)
        species_layout.addWidget(self.DonotdetectButton)
        species_layout.addWidget(self.AssociateSpButton)

        center_layout.addLayout(species_layout)
        center_layout.addSpacing(12)
        GapLayout=QtWidgets.QHBoxLayout()
        self.GapOpenLabel=QtWidgets.QLabel("Gap Opening Penalty:")
        self.GapOpenLabel.setFont(QtGui.QFont("Arial",12,QtGui.QFont.Bold))
        self.GapOpenSpin=QtWidgets.QSpinBox()
        self.GapOpenSpin.setRange(1, 100)
        self.GapOpenSpin.setValue(10)

        self.GapExtendLabel=QtWidgets.QLabel("Gap Extension Penalty:")
        self.GapExtendLabel.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
        self.GapExtendSpin=QtWidgets.QSpinBox()
        self.GapExtendSpin.setRange(1, 100)
        self.GapExtendSpin.setValue(1)

        GapLayout.addWidget(self.GapOpenLabel)
        GapLayout.addWidget(self.GapOpenSpin)
        GapLayout.addWidget(self.GapExtendLabel)
        GapLayout.addWidget(self.GapExtendSpin)
        self.GapGroup=QtWidgets.QWidget()
        self.GapGroup.setLayout(GapLayout)
        center_layout.addWidget(self.GapGroup)

        self.GapGroup.setVisible(False)
        self.myDetectSpeciesMode=0
        self.DetectButton.toggled.connect(self.setDetectmode)
        self.DonotdetectButton.toggled.connect(self.setdonotdetectMode)
        self.AssociateSpButton.toggled.connect(self.setspeciesassociateMode)


        main_layout.addStretch()  
        main_layout.addLayout(center_layout)
        main_layout.addStretch()  

        button_layout=QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        self.runbtn=QtWidgets.QPushButton("Cluster!")
        self.runbtn.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
        self.runbtn.setFixedWidth(180)
        self.runbtn.clicked.connect(self.fix_orient) 
        button_layout.addWidget(self.runbtn)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        options_widget.setLayout(main_layout)
        self.stack.addWidget(options_widget)
        self.opt_screen_index=self.stack.indexOf(options_widget)

    def initExternalOptionsScreen(self):
        options_widget=QtWidgets.QWidget()
        main_layout=QtWidgets.QVBoxLayout(options_widget)
        main_layout.setContentsMargins(40,40,40,40)

        top_layout=QtWidgets.QHBoxLayout()
        self.reset_button2=self.makeResetButton()


        self.extloadedlabel=QtWidgets.QLabel("")
        self.extloadedlabel.setFont(QtGui.QFont("Arial",14,QtGui.QFont.Bold))
        self.extloadedlabel.setAlignment(Qt.AlignCenter)

        top_layout.addWidget(self.reset_button2, alignment=Qt.AlignLeft)
        top_layout.addStretch()
        top_layout.addWidget(self.extloadedlabel, alignment=Qt.AlignCenter)
        top_layout.addStretch()

        main_layout.addLayout(top_layout)

        center_layout=QtWidgets.QVBoxLayout()
        center_layout.setAlignment(Qt.AlignCenter)

        MinOverlapLayout=QtWidgets.QHBoxLayout()
        self.MinOverlapLabel2=QtWidgets.QLabel("Minimum Overlap:")
        self.MinOverlapLabel2.setFont(QtGui.QFont("Arial",12,QtGui.QFont.Bold))
        self.MinOverlapTextBox2=QtWidgets.QLineEdit("100")
        self.MinOverlapTextBox2.setFixedWidth(80)
        self.overlaplen=100
        MinOverlapLayout.addWidget(self.MinOverlapLabel2)
        MinOverlapLayout.addWidget(self.MinOverlapTextBox2)
        MinOverlapLayout.addStretch()
        center_layout.addLayout(MinOverlapLayout)
        ProcLayout2=QtWidgets.QHBoxLayout()
        self.ProcLabel2=QtWidgets.QLabel("Number of processors:")
        self.ProcLabel2.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))

        self.ProcCombo2=QtWidgets.QComboBox()
        max_procs=mp.cpu_count()
        default_procs=min(4, max_procs)
        for i in range(1, max_procs+1):
            self.ProcCombo2.addItem(str(i))
        self.ProcCombo2.setCurrentText(str(default_procs))
        self.ProcCombo2.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                      QtWidgets.QSizePolicy.Fixed)

        ProcLayout2.addWidget(self.ProcLabel2)
        ProcLayout2.addWidget(self.ProcCombo2)
        ProcLayout2.addStretch()
        center_layout.addSpacing(12)
        center_layout.addLayout(ProcLayout2)
        species_layout=QtWidgets.QHBoxLayout()
        self.species_label2=QtWidgets.QLabel("Species Names in my project file:")
        self.species_label2.setFont(QtGui.QFont("Arial",12,QtGui.QFont.Bold))
        self.DetectButton2=QtWidgets.QRadioButton("Detect")
        self.DetectButton2.setChecked(True)
        self.DonotdetectButton2=QtWidgets.QRadioButton("Do not detect")
        self.AssociateSpButton2=QtWidgets.QRadioButton("Add species names by file")

        species_layout.addWidget(self.species_label2)
        species_layout.addWidget(self.DetectButton2)
        species_layout.addWidget(self.DonotdetectButton2)
        species_layout.addWidget(self.AssociateSpButton2)
        center_layout.addLayout(species_layout)
        center_layout.addSpacing(12)
        GapLayout=QtWidgets.QHBoxLayout()
        self.GapOpenLabel=QtWidgets.QLabel("Gap Opening Penalty:")
        self.GapOpenLabel.setFont(QtGui.QFont("Arial",12,QtGui.QFont.Bold))
        self.GapOpenSpin2=QtWidgets.QSpinBox()
        self.GapOpenSpin2.setRange(1, 100)
        self.GapOpenSpin2.setValue(10)

        self.GapExtendLabel=QtWidgets.QLabel("Gap Extension Penalty:")
        self.GapExtendLabel.setFont(QtGui.QFont("Arial",12,QtGui.QFont.Bold))
        self.GapExtendSpin2=QtWidgets.QSpinBox()
        self.GapExtendSpin2.setRange(1, 100)
        self.GapExtendSpin2.setValue(1)

        GapLayout.addWidget(self.GapOpenLabel)
        GapLayout.addWidget(self.GapOpenSpin2)
        GapLayout.addWidget(self.GapExtendLabel)
        GapLayout.addWidget(self.GapExtendSpin2)
        center_layout.addLayout(GapLayout)
        self.myDetectSpeciesMode2=0
        self.DetectButton2.toggled.connect(lambda: setattr(self,"myDetectSpeciesMode2",0))
        self.DonotdetectButton2.toggled.connect(lambda: setattr(self,"myDetectSpeciesMode2",1))
        self.AssociateSpButton2.toggled.connect(lambda: setattr(self,"myDetectSpeciesMode2",2))

        main_layout.addStretch()
        main_layout.addLayout(center_layout)
        main_layout.addStretch()

        button_layout=QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        self.runbtn2=QtWidgets.QPushButton("Cluster!")
        self.runbtn2.setFont(QtGui.QFont("Arial",12,QtGui.QFont.Bold))
        self.runbtn2.setFixedWidth(180)
        self.runbtn2.clicked.connect(self.fix_orient)
        button_layout.addWidget(self.runbtn2)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        options_widget.setLayout(main_layout)
        self.stack.addWidget(options_widget)
        self.externaloptsindex=self.stack.indexOf(options_widget)


    def initExternalSpeciesScreen(self):
        widget=QtWidgets.QWidget()
        vbox=QtWidgets.QVBoxLayout(widget)
        vbox.setContentsMargins(40,40,40,40)
        vbox.setAlignment(Qt.AlignTop)
        reset_btn=self.makeResetButton()
        vbox.insertWidget(0, reset_btn, alignment=Qt.AlignLeft)
        self.exttitle=QtWidgets.QLabel("")
        self.exttitle.setFont(QtGui.QFont("Arial",18,QtGui.QFont.Bold))
        self.exttitle.setAlignment(Qt.AlignCenter)
        vbox.addWidget(self.exttitle)

        question=QtWidgets.QLabel("Before further processing do you want to exclude any species names?")
        question.setFont(QtGui.QFont("Arial",14))
        question.setAlignment(Qt.AlignCenter)
        vbox.addWidget(question)

        self.extselectall=QtWidgets.QCheckBox("Select all")
        self.extselectall.setChecked(True)
        self.extselectall.stateChanged.connect(self.toggle_all_species)
        vbox.addWidget(self.extselectall)

        self.extincludeundetected=QtWidgets.QCheckBox("Include sequences with undetected names")
        self.extincludeundetected.setChecked(True)
        vbox.addWidget(self.extincludeundetected)

        self.extscroll=QtWidgets.QScrollArea()
        self.extscroll.setWidgetResizable(True)
        self.extscrollwidget=QtWidgets.QWidget()
        self.extscrollvbox=QtWidgets.QVBoxLayout(self.extscrollwidget)
        self.extscroll.setWidget(self.extscrollwidget)
        vbox.addWidget(self.extscroll)
        self.extsearch=QtWidgets.QLineEdit()
        self.extsearch.setPlaceholderText("Search species...")
        self.extsearch.textChanged.connect(self.filter_species_list)
        vbox.addWidget(self.extsearch)
        self.extspecies_checks={} 

        proceed_btn=QtWidgets.QPushButton("Proceed")
        proceed_btn.clicked.connect(self.finish_external_species)
        vbox.addWidget(proceed_btn,alignment=Qt.AlignCenter)

        self.stack.addWidget(widget)
        self.externalspeciesindex=self.stack.indexOf(widget)
    def filter_species_list(self,text):
        text=text.strip().lower()
        for sp,cb in self.extspecieschecks.items():
            cb.setVisible(text in sp.lower() or text=="")

    def toggle_all_species(self,state):
        for cb in self.extspecies_checks.values():
            cb.setChecked(state==QtCore.Qt.Checked)

    def finish_external_species(self):
        self.extspeciesselected=[sp for sp,cb in self.extspecieschecks.items() if cb.isChecked()]
        includeundetected=self.extincludeundetected.isChecked()

        filtered={}
        for extid, seq in self.extsequences.items():
            sp=self.extspeciesmap.get(extid)
            if (sp in self.extspeciesselected) or (sp is None and includeundetected):
                filtered[extid]=seq

        self.extsequences=filtered
        self.extcounts=len(filtered)

        print("After filtering, external sequences:", self.extcounts)
        self.extmodetitle.setText(
            f"External sequences before filtering: {self.extbeforecount}\n"
            f"After filtering: {self.extcounts}"
        )
        self.stack.setCurrentIndex(self.externalmodeindex)

    def runExternalHomologyAssume(self):
        if not self.runroot:
            self.runroot=_mk_run_root(self.infilename)
        combpath=os.path.join(self.runroot,"combined.fa")
        with open(combpath,"w") as out:
            if not getattr(self,"sequences",{}):
                self.loadseqs(self.infilename)
                self.projectcount=self.seqcounts
            for sid,seq in self.sequences.items():
                out.write(">"+sid+"\n")
                for i in range(0,len(seq),80):
                    out.write(seq[i:i+80]+"\n")
            for sid,seq in self.extsequences.items():
                out.write(">"+sid+"\n")
                for i in range(0,len(seq),80):
                    out.write(seq[i:i+80]+"\n")

        self.infilename=combpath
        self.mode="hom"
        self.loadseqs(combpath)

        self.extloadedlabel.setText(
            "Loaded "+str(self.projectcount)+" project sequences+"+
            str(len(self.extsequences))+" external sequences"
        )
        self.stack.setCurrentIndex(self.externaloptsindex)
    def writeExternalSubset(self):
        if not self.runroot:
            self.runroot=_mk_run_root(self.infilename)
        extpath=os.path.join(self.runroot,"external.filtered.fa")
        with open(extpath,"w") as out:
            for sid,seq in self.extsequences.items():
                out.write(">"+sid+"\n")
                for i in range(0,len(seq),80):
                    out.write(seq[i:i+80]+"\n")
        return extpath

    def updaterunbuttonformodes(self):
        try:
            self.runbtn.clicked.disconnect()
        except TypeError:
            pass

        if getattr(self, "mode", None)=="frag":
            self.runbtn.setText("Homology Search…")
            self.runbtn.clicked.connect(self.openhomologysettings)
        else:
            self.runbtn.setText("Cluster!")
            self.runbtn.clicked.connect(self.fix_orient)
    def resetToStart(self):
        self.infilename=None
        self.indir=None
        self.sequences={}
        self.seqdict={}
        self.seqiddict={}
        self.seqdict1={}      
        self.seqids=[]        
        self.seqcounts=0
        self.len_aln=None
        self.refseq=""
        self.mode=None
        self.overlaplen=100
        self.hasN_flags={}

        self.spassocs={}
        self.spassocs2={}
        self.lengths={}
        self.externalinfilename=None
        self.extbeforecount=0
        self.extsequences={}
        self.extseqdict={}
        self.extseqiddict={}
        self.extspeciesmap={}
        self.extspecieschecks={}
        self.extcounts=0

        self.projectcount=0

        self._hom_input_fasta=None
        self._hom_input_count=0
        self._blast_query=None
        self._blast_db=None
        self._blast_opts={}
        self.exthomologymode=None
        try:
            self.GapOpenSpin.setValue(10)   
            self.GapExtendSpin.setValue(1)
        except Exception:
            pass
        try:
            self.GapOpenSpin2.setValue(10)
            self.GapExtendSpin2.setValue(1)
        except Exception:
            pass
        try: self.loaded_label.setText("")
        except: pass
        try: self.extloadedlabel.setText("")
        except: pass
        try: self.exttitle.setText("")
        except: pass
        try:
            os.chdir(os.path.dirname(os.path.abspath(__file__)))
        except Exception:
            pass
        for attr in ("brunner", "hrunner", "mymeasuredist", "mycluster"):
            if hasattr(self, attr):
                try:
                    getattr(self, attr).cancel()
                except Exception:
                    pass

        if hasattr(self, "_force_mode_on_load"):
            del self._force_mode_on_load
        self._prev_cwd=None
        self.runroot=None
        self.stack.setCurrentIndex(0)


    def openblastsettings(self):
        blast_dir=os.path.join(self.runroot, "blast")
        os.makedirs(blast_dir, exist_ok=True)

        self.bmsg=HomologyJobDialog(
            self,
            title="BLAST search",
            subtitle=f"Output folder: {blast_dir}"
        )

        default_prefix=os.path.join(blast_dir, "out")
        dlg=BlastSettingsDialog(
            self,
            indir=getattr(self, "indir", ""),
            fasta_path=getattr(self, "infilename", ""),
            default_prefix=default_prefix
        )
        if dlg.exec_()==QtWidgets.QDialog.Accepted:
            self._blast_opts=dlg.params()
            extfile=self.writeExternalSubset()
            self._blast_query=self.infilename
            self._blast_db=extfile

            self.bmsg.setOutdir(os.path.dirname(self._blast_opts["outprefix"]))
            self.bmsg.cancelRequested.connect(self.cancelBlast)
            self.bmsg.show()

            self.brunner=BlastRunner(self._blast_query, self._blast_db, self._blast_opts, self)
            self.brunner.notifyLine.connect(self.bmsg.appendLine)
            self.brunner.taskFinished.connect(self.blastFinished)
            self.brunner.start()
    def cancelBlast(self):
        if hasattr(self, "brunner"):
            self.brunner.cancel()
        if hasattr(self, "bmsg"):
            self.bmsg.appendLine("Cancellation requested…")
            try:
                self.bmsg.setSubtitle("Cancelling… Please wait")
                self.bmsg.progress.setRange(0, 0)
            except Exception:
                pass

        def _wait_proc():
            alive=hasattr(self, "brunner") and self.brunner._proc and (self.brunner._proc.poll() is None)
            if alive:
                QtCore.QTimer.singleShot(200, _wait_proc)
                return
            try:
                if hasattr(self, "bmsg"):
                    self.bmsg.close()
            except Exception:
                pass
            self.resetToStart()

        QtCore.QTimer.singleShot(200, _wait_proc)

    def blastFinished(self, rc, outprefix):
        if rc != 0:
            QtWidgets.QMessageBox.critical(self, "BLAST search", "BLAST failed.")
            return

        finalfa=outprefix+".final.fa"
        if not os.path.exists(finalfa):
            QtWidgets.QMessageBox.warning(self, "BLAST search", "No final.fa was produced.")
            return

        try:
            orig=getattr(self, "extbeforecount", None) or _count_fasta_records(self._blast_db)
        except Exception:
            orig=None
        outn=_count_fasta_records(finalfa)
        trimmed=max(0, (orig or 0) - outn)

        lines=[]
        if orig is not None:
            lines.append(f"Original external sequences: {orig}")
        lines.append(f"Output homolog windows (BLAST): {outn}")
        if orig is not None:
            lines.append(f"Trimmed/filtered away: {trimmed}")
        summary="\n".join(lines)

        self._externalHomologyProceed(finalfa, summary)

        try:
            if hasattr(self, "bmsg"):
                self.bmsg.appendLine(summary.replace("\n", " | "))
                self.bmsg.showSummary(summary)
        except Exception:
            pass

        try:
            if hasattr(self, "bmsg"):
                self.bmsg.close()
        except Exception:
            pass


    def openhomologysettings(self):
        hom_dir=os.path.join(self.runroot, "homology")
        os.makedirs(hom_dir, exist_ok=True)

        self.hmsg=HomologyJobDialog(
            self,
            title="Homology search",
            subtitle=f"Output folder: {hom_dir}"
        )

        default_prefix=os.path.join(hom_dir, "out")
        dlg=HomologySettingsDialog(
            self,
            indir=getattr(self, "indir", ""),
            fasta_path=getattr(self, "infilename", ""),
            default_prefix=default_prefix
        )
        if dlg.exec_()==QtWidgets.QDialog.Accepted:
            self.starthomologysearch(dlg.params())

    def _externalHomologyProceed(self, final_fa, summary):
        if not os.path.exists(final_fa):
            QtWidgets.QMessageBox.warning(self,"Homology","No final.fa was produced.")
            return
        self.extcounts=0
        combpath=os.path.join(self.runroot,"combined.fa")
        with open(combpath,"w") as out:
            if not getattr(self,"sequences",{}):
                self.loadseqs(self.infilename)
                self.projectcount=self.seqcounts
            for sid,seq in self.sequences.items():
                out.write(">"+sid+"\n")
                for i in range(0,len(seq),80):
                    out.write(seq[i:i+80]+"\n")
            for sid,seq in self.readfasta(final_fa):
                out.write(">"+sid+"\n")
                self.extcounts+=1
                for i in range(0,len(seq),80):
                    out.write(seq[i:i+80]+"\n")


        self.infilename=combpath
        self.mode="hom"
        self.loadseqs(combpath)

        self.extloadedlabel.setText(
            "Loaded "+str(self.projectcount)+" project sequences+"+
            str(self.extcounts)+" external sequences"
        )
        self.stack.setCurrentIndex(self.externaloptsindex)
        try:
            if hasattr(self, "hmsg"):
                self.hmsg.close()
        except Exception:
            pass

    def readfasta(self,path):
        seqid=""
        seq=""
        with open(path) as fh:
            for line in fh:
                if line.startswith(">"):
                    if seqid:
                        yield seqid,seq
                    seqid=line.strip()[1:]
                    seq=""
                else:
                    seq+=line.strip()
            if seqid:
                yield seqid,seq
    def starthomologysearch(self, opts):
        self._homology_opts=opts

        hom_dir=os.path.join(self.runroot, "homology")
        os.makedirs(hom_dir, exist_ok=True)
        opts["outprefix"]=os.path.join(hom_dir, "out")

        self.hmsg.setOutdir(hom_dir)
        self.hmsg.cancelRequested.connect(self.cancelHomology)
        self.hmsg.show()

        self.hrunner=EdlibHomologyRunner(self._hom_input_fasta, opts, self)
        self.hrunner.notifyLine.connect(self.hmsg.appendLine)
        self.hrunner.taskFinished.connect(self.homologyFinished)
        self.hrunner.start()
    def updateStatusLabel(self, msg: str):
        self.progressLabel.setText(msg)
    def cancelHomology(self):
        if hasattr(self, "hrunner"):
            try:
                self.hrunner.cancel()
            except Exception as e:
                print(f"[cancelHomology] cancel() failed: {e}")

        if hasattr(self, "hmsg"):
            try:
                self.hmsg.appendLine("Cancellation requested…")
                self.hmsg.setSubtitle("Cancelling… Please wait")
                self.hmsg.progress.setRange(0, 0)  # bounce mode
                QtWidgets.QApplication.processEvents()
            except Exception:
                pass
        def _wait_until_done():
            if hasattr(self, "hrunner") and self.hrunner.isRunning():
                QtCore.QTimer.singleShot(200, _wait_until_done)
                return
            try:
                if hasattr(self, "hmsg"):
                    self.hmsg.close()
            except Exception:
                pass
            self.resetToStart()

        QtCore.QTimer.singleShot(200, _wait_until_done)

    def homologyFinished(self, rc, outprefix):
        if rc != 0:
            try:
                if hasattr(self, "hmsg"):
                    self.hmsg.appendLine("Failed (non-zero return code).")
            except Exception:
                pass
            QtWidgets.QMessageBox.critical(self, "Homology search", "edlib search failed.")
            return

        final_fa=outprefix+".final.fa"

        def _count_fasta_records(path: str) -> int:
            n=0
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                for line in fh:
                    if line.startswith(">"):
                        n+=1
            return n

        try:
            orig=getattr(self, "_hom_input_count", None) or _count_fasta_records(getattr(self, "_hom_input_fasta", self.infilename))
        except Exception:
            orig=None
        outn=_count_fasta_records(final_fa) if os.path.exists(final_fa) else 0
        trimmed=max(0, (orig or 0) - outn)

        lines=[]
        if orig is not None:
            lines.append(f"Original sequences: {orig}")
        lines.append(f"Output sequences (homolog windows): {outn}")
        lines.append(f"Trimmed/filtered away: {trimmed}")
        summary="\n".join(lines)

        try:
            if hasattr(self, "hmsg"):
                self.hmsg.appendLine(summary.replace("\n", " | "))
                self.hmsg.showSummary(summary)
                try:
                    self.hmsg.proceedRequested.disconnect()
                except Exception:
                    pass
                try:
                    self.hmsg.finishRequested.disconnect()
                except Exception:
                    pass
                if getattr(self,"exthomologymode",0)==2:
                    print("sadfdsf")
                    self.hmsg.proceedRequested.connect(lambda: self._externalHomologyProceed(final_fa, summary))
                else:
                    self.hmsg.proceedRequested.connect(lambda: self._homologyProceed(final_fa))
                self.hmsg.finishRequested.connect(lambda: self._homologyFinish(summary))
        except Exception:
            pass
    def externalHomologyDone(self,rc,outprefix):
        if rc!=0:
            QtWidgets.QMessageBox.warning(self,"Homology","External homology failed")
            return
        finalfa=outprefix+".final.fa"
        if not os.path.exists(finalfa):
            QtWidgets.QMessageBox.warning(self,"Homology","No final.fa produced")
            return

        if not getattr(self,"sequences",{}):
            self.loadseqs(self.infilename)
            self.projectcount=self.seqcounts

        combpath=os.path.join(self.runroot,"combined.fa")
        with open(combpath,"w") as out:
            for sid,seq in self.sequences.items():
                out.write(">"+sid+"\n")
                for i in range(0,len(seq),80):
                    out.write(seq[i:i+80]+"\n")
            for sid,seq in parse_fasta(finalfa):
                out.write(">"+sid+"\n")
                for i in range(0,len(seq),80):
                    out.write(seq[i:i+80]+"\n")

        self.infilename=combpath
        self.mode="hom"
        self.loadseqs(combpath)

        self.extloadedlabel.setText(
            "Loaded "+str(self.projectcount)+" project sequences+"+
            str(_count_fasta_records(finalfa))+" external sequences"
        )
        self.stack.setCurrentIndex(self.externaloptsindex)

    def _homologyFinish(self, summary: str):
        try:
            if hasattr(self, "hmsg"):
                self.hmsg.close()
        except Exception:
            pass

        summary+=(
            "\n\nPlease also check the histogram tsv and "
            "the file 'excluded.original.fa' to ensure no critical sequences "
            "were lost. If important sequences are missing, ensure homology before adding them back into your FASTA"
        )
        QtWidgets.QMessageBox.information(self, "Run summary", summary)

        try:
            self.resetToStart()
        except Exception:
            pass
    def _homologyProceed(self, final_fa: str):
        if not os.path.exists(final_fa):
            QtWidgets.QMessageBox.warning(self, "Homology search", "No final.fa was produced.")
            return

        msg=QtWidgets.QMessageBox(self)
        msg.setWindowTitle("Check your results")
        msg.setIcon(QtWidgets.QMessageBox.Warning)
        msg.setText(
            "Before proceeding to clustering:\n\n"
            "--> Review the histogram files.\n"
            "--> Inspect 'excluded.original.fa' to ensure no critical sequences were lost.\n\n"
            "If important sequences are missing, ensure homology before adding them back into your FASTA and cluster."
        )
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        choice=msg.exec_()

        if choice==QtWidgets.QMessageBox.Cancel:
            try:
                if hasattr(self, "hmsg"):
                    self.hmsg.close()
            except Exception:
                pass
            self.stack.setCurrentIndex(0)
            return

        self.infilename=final_fa
        self.mode="hom"
        self.GapGroup.setVisible(True) 
        self._force_mode_on_load="hom"
        self.loadseqs(final_fa)
        self.stack.setCurrentIndex(self.opt_screen_index)
        try:
            self.updaterunbuttonformodes()
        except Exception:
            pass
        try:
            if hasattr(self, "hmsg"):
                self.hmsg.close()
        except Exception:
            pass

    
    def setoverlaplen(self, string):
        self.overlaplen=int(string)

    def setDetectmode(self):
        self.myDetectSpeciesMode=0

    def setdonotdetectMode(self):
        self.myDetectSpeciesMode=1

    def setspeciesassociateMode(self):
        if self.AssociateSpButton.isChecked(): 
            self.myDetectSpeciesMode=2
            self.openspfile()
    def openspfile(self):
        fname=QtWidgets.QFileDialog.getOpenFileName(self, 'Load species association csv', "")
        if len(fname)>0:
            self.spfile=str(fname[0])
            self.assocspfile(self.spfile)
    def assocspfile(self,infile):

        try:
            self.spassocs2={}
            with open(infile) as infile:
                l=infile.readlines()
                for each in l:
                    m=each.strip().split("\t")
                    self.spassocs2[m[0]]=m[1]
        except:
            pass

    def goBackToFileSelection(self):
        self.stack.setCurrentIndex(0)

    def cluster_action(self):
        print("Clustering Started!")
 


    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls=event.mimeData().urls()
        if urls:
            self.infilename=str(urls[0].toLocalFile())  
            self.indir=os.path.dirname(os.path.abspath(self.infilename))
            self.runroot=_mk_run_root(self.infilename)

            print("Selected:", self.infilename)
            self.stack.setCurrentIndex(self.external_screen_index)

    def loadseqs(self, infilename):
        self.seqiddict, self.seqdict, self.sequences={}, {}, {}
        self.seqcounts=0
        self.refseq=""
        self.seqdict1={}
        self.seqids=[]
        self.lengths={}
        self.len_aln=0
        sequence=""
        seqid=None
        try:
            with open(infilename, "r", encoding="utf-8", errors="ignore") as fh:
                for line in fh:
                    if line.startswith(">"):
                        if seqid is not None:
                            if self.len_aln==0:
                                self.len_aln=len(sequence)
                            self.lengths[len(sequence)]=""
                            tempseq, s, e=bsm.change_ext_gaps(sequence)
                            self.seqdict.setdefault(tempseq, []).append(str(self.seqcounts))
                            self.sequences[seqid]=sequence
                            if self.seqcounts==0:
                                self.refseq=tempseq
                            self.seqiddict[str(self.seqcounts)]=seqid
                            self.seqcounts+=1
                        seqid=line.strip()[1:].replace('"', "").replace("'", "")
                        sequence=""
                    else:
                        sequence+=line.strip().upper()
                if seqid is not None:
                    if self.len_aln==0:
                        self.len_aln=len(sequence)
                    self.lengths[len(sequence)]=""
                    tempseq, s, e=bsm.change_ext_gaps(sequence)
                    self.seqdict.setdefault(tempseq, []).append(str(self.seqcounts))
                    self.sequences[seqid]=sequence
                    self.seqiddict[str(self.seqcounts)]=seqid
                    self.seqcounts+=1
            self.seqdict1=self.seqdict

            self.loaded_label.setText(f"Loaded {self.seqcounts} sequences")
            print(f"[loadseqs] alignment length={self.len_aln}")

        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Message", f"Invalid FASTA file:\n{e}")
            return
        if getattr(self, "_force_mode_on_load", None):
            self.mode=self._force_mode_on_load
            delattr(self, "_force_mode_on_load")
            self.stack.setCurrentIndex(1)
            return


        


    def showpairdialog(self,pairs):
        dialog=PairTableDialog(pairs)
        self.msgBox.close()
        dialog.exec_()

    def ask_short_species_names(self, names):
        dlg=QtWidgets.QDialog(self)
        dlg.setWindowTitle("Confirm short species names")
        layout=QtWidgets.QVBoxLayout(dlg)
        msg=QtWidgets.QLabel( "The following species names are unusually short (7 characters).\n"
            "Do you want to accept these as species names?")
        msg.setWordWrap(True)
        layout.addWidget(msg)
        table=QtWidgets.QTableWidget(len(names), 1, dlg)
        table.setHorizontalHeaderLabels(["Species name"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        for row, name in enumerate(sorted(names)):
            item=QtWidgets.QTableWidgetItem(name)
            table.setItem(row, 0, item)
        table.resizeColumnsToContents()
        table.setMinimumWidth(250)
        table.setMaximumHeight(300) 
        layout.addWidget(table)
        btns=QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Yes|QtWidgets.QDialogButtonBox.No)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)
        return dlg.exec_()==QtWidgets.QDialog.Accepted


    def runcluster(self):
        bsm.set_parasail_gaps(self.GapOpenSpin.value(), self.GapExtendSpin.value())
        self.overlaplen=int(self.MinOverlapTextBox.text())
        try:
            self.nprocs=int(self.ProcCombo.currentText())
        except AttributeError:
            self.nprocs=int(self.ProcCombo2.currentText())
        print("Overlap is",self.overlaplen)
        checkstatus=bsm.checkmatrix(self.len_aln,self.seqdict1)
        self.gapmode="m" 
        cluster_dir=os.path.join(self.runroot or _mk_run_root(self.infilename), "cluster")
        os.makedirs(cluster_dir, exist_ok=True)
        iddict_name=f"{Path(self.infilename).stem}_iddict.txt"
        with open(os.path.join(cluster_dir, iddict_name), 'w') as outfile:
            for each in self.seqiddict.keys():
                outfile.write(each+' : '+self.seqiddict[each]+'\n')
        if self.myDetectSpeciesMode==0:
            pattern=r"[A-Z][a-z]*[ _-][a-z][a-z]*"
            self.spassocs={}
            shortnames=set()
            for seqid in self.seqiddict.keys():
                spname=re.findall(pattern,self.seqiddict[seqid])
                if len(spname)>0:
                    spname=spname[0]
                else:
                    spname=""
                self.spassocs[seqid]=spname
                if spname!="" and len(spname)<=7:
                    shortnames.add(spname)
            if shortnames:
                keep=self.ask_short_species_names(shortnames)
                if not keep:
                    for seqid,spname in self.spassocs.items():
                        if spname in shortnames:
                            self.spassocs[seqid]=""
        if self.myDetectSpeciesMode==1:
            self.spassocs={}
            for seqid in self.seqiddict.keys():
                self.spassocs[seqid]=""
        if self.myDetectSpeciesMode==2:
            self.spassocs={}
            for seqid in self.seqiddict.keys():
                try:
                    self.spassocs[seqid]=self.spassocs2[self.seqiddict[seqid]]
                except KeyError:
                    self.spassocs[seqid]=""

        self.pdist()

    def fix_orient(self):
        if self.mode!="aligned":
            self.seqdict1={}
            tempdict={}
            ambiguity_codes=[("R", "A"), ("R", "G"),("M", "A"), ("M", "C"),("S", "C"), ("S", "G"),("Y", "C"), ("Y", "T"),("K", "G"), ("K", "T"),("W", "A"), ("W", "T"),("V", "A"), ("V", "C"),("V", "G"),("H", "A"),("H", "C"),("H", "T"),("D", "A"), ("D", "G"),("D", "T"), ("B", "C"),("B", "G"), ("B", "T"),("N", "A"), ("N", "G"), ("N", "C"), ("N", "T")]
            for seq in self.seqdict.keys():
                s=seq.replace("?", "").replace("-", "")
                s=simpifyambs(s)   
                if not s:
                    continue
                d1=bsm.align_score(s, self.refseq, mode="sg_stats").score
                rc=bsm.rev_comp(s)
                d2=bsm.align_score(rc, self.refseq, mode="sg_stats").score

                if d1<=d2:
                    try:
                        tempdict[s]+=self.seqdict[seq]
                    except KeyError:
                        tempdict[s]=self.seqdict[seq]
                if d2<d1:
                    try:
                        tempdict[rc]+=self.seqdict[seq]
                    except KeyError:
                        tempdict[rc]=self.seqdict[seq]
            for k in tempdict.keys():
                m=tempdict[k]
                m.sort()
                self.seqdict1[k]=m
                self.hasN_flags[k]=("N" in k)
        else:
            self.seqdict1=self.seqdict
        self.seqids=list(self.seqdict1.values())

        self.runcluster()

    def pdist(self):
        self.msgBox=CancelableMsgBox(self, on_cancel=self.cancel_task)
        cancel_button=QtWidgets.QPushButton("Cancel")
        cancel_button.clicked.connect(self.msgBox.trigger_cancel)
        self.msgBox.addButton(cancel_button, QtWidgets.QMessageBox.RejectRole)


        l=self.msgBox.layout()
        self.pbar=QtWidgets.QProgressBar()
        l.addWidget(self.pbar, l.rowCount(), 0, 1, l.columnCount(), QtCore.Qt.AlignCenter)
        self.pbar.setRange(0, 0) 
        self.msgBox.show()
        QtWidgets.QApplication.processEvents() 
        if not self.runroot:
            self.runroot=_mk_run_root(self.infilename)

        args=(
            self.seqdict1,
            self.seqiddict,
            self.hasN_flags,
            self.overlaplen,
            self.mode,
            self.gapmode,
            self.nprocs,
            self.runroot,
        )

        self.dist_starter=DistanceStarter(args, self)
        self.dist_starter.progressUpdated.connect(self.updatepbar)
        self.dist_starter.statusUpdated.connect(self.msgBox.setText)

        self.dist_starter.doneWithResult.connect(self.cluster)
        self.dist_starter.finishedOK.connect(self.msgBox.close)

        def _on_cancel_finish():
            print("cancel")
            try:
                print("c2")
                self.msgBox.setText("Cancelling… Please wait")
                self.pbar.setRange(0, 0)
                self.msgBox.setStandardButtons(QtWidgets.QMessageBox.NoButton)
                QtWidgets.QApplication.processEvents()
                self.msgBox.repaint()
            except Exception:
                print("c3")
                pass
            def _wait_until_done():
                print("c4")

                if self.dist_starter.isRunning():
                    print("c5")
                    QtCore.QTimer.singleShot(300, _wait_until_done)
                    return
                try:
                    print("c6")
                    self.msgBox.setText("Cancelled.")
                    QtWidgets.QApplication.processEvents()
                    time.sleep(0.3)
                    self.msgBox.close()
                except Exception:
                    print("c7")
                    pass
                self.resetToStart()
            QtCore.QTimer.singleShot(300, _wait_until_done)

        self.dist_starter.finishedWithCancel.connect(_on_cancel_finish)
        self.dist_starter.finishedWithError.connect(lambda msg: (self.msgBox.close(),QtWidgets.QMessageBox.critical(self, "Error", msg)))
        cancel_button.clicked.connect(self.dist_starter.cancel)


        self.dist_starter.start()


        
    def cancel_task(self):
        if getattr(self, "dist_starter", None):
            try:
                self.dist_starter.cancel()
            except Exception as e:
                print(f"[WARN] cancel_task failed: {e}", file=sys.stderr, flush=True)
        else:
            print("[INFO] cancel_task called, but dist_starter is None (already cleaned up)", file=sys.stderr, flush=True)



    def cluster(self,overlaperror):
        if isinstance(overlaperror, list) and overlaperror and overlaperror[0][0]=="CANCELLED":
            return
        if not overlaperror:
            self.msgBox=CancelableMsgBox(self, on_cancel=self.cancel_task)
            self.msgBox.setText("Clustering...")
            self.pbar=QtWidgets.QProgressBar()
            l=self.msgBox.layout()
            l.addWidget(self.pbar, l.rowCount(), 0, 1, l.columnCount(), QtCore.Qt.AlignCenter)
            self.pbar.setRange(0, 100)
            self.pbar.setValue(0)
            self.msgBox.show()
            minthresh=0
            maxthresh=100
            cluster_dir=os.path.join(self.runroot, "cluster")
            os.makedirs(cluster_dir, exist_ok=True)

            self._prev_cwd=os.getcwd()
            os.chdir(self.runroot)
            inname_for_cluster="Results"
            pdistdir=os.path.join(self.runroot, "pmatrix")
            self.mycluster=clust.rungene(self.seqids,self.sequences,pdistdir,self.seqcounts,self.seqiddict,inname_for_cluster,minthresh,maxthresh,self.spassocs)
            self.mycluster.notifyRange.connect(self.setpbarrange)
            self.mycluster.notifyProgress.connect(self.updatepclustbar)
            try:
                self.mycluster.notifyProgress.disconnect(self.updatepclustbar)
            except Exception:
                pass
            self.mycluster.notifyProgress.connect(self.updatepclustbar, QtCore.Qt.QueuedConnection)
            self.mycluster.notifySwitch.connect(self.setpbartext)
            self.mycluster.taskFinished.connect(self.openbrowser)
            self.mycluster.start()
        else:
            self.showpairdialog(overlaperror)

    def updatepclustbar(self,i):
        self.pbar.setValue(i)

    def setpbarrange(self,rangevalue):
        self.pbar.setRange(0, rangevalue)

    def setpbartext(self,text):
        self.msgBox.setText(text)

    def updatepbar(self, i):
        if i==-2:
            self.pbar.setRange(0, 0)
            return
        elif i==-1:
            self.pbar.setRange(0, 100)
            self.pbar.setValue(0)
            return
        else:
            self.pbar.setRange(0, 100)
            self.pbar.setValue(i)



     
    def openbrowser(self, i):
        self.msgBox.close()
        html_src=Path(resource_path("IntegraTaxViz.html")).resolve()
        js_src=Path(resource_path("js")) 
        runroot=self.runroot
        itvfile=Path(runroot) / "Results.itv"
        html_copy=Path(runroot) / "IntegraTaxViz.html"
        js_dest=Path(runroot) / "js"
        if not js_dest.exists():
            shutil.copytree(js_src, js_dest)
        with open(html_src, "r", encoding="utf-8") as f:
            html_content=f.read()

        injected=html_content.replace( "</head>",f"<script>window.__RESULTS_PATH__=String.raw`{itvfile}`;</script>\n</head>")
        with open(html_copy, "w", encoding="utf-8") as f:
            f.write(injected)
        webbrowser.open(html_copy.as_uri())
        self.resetToStart()


def main():
    QtWidgets.QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QtWidgets.QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app=QtWidgets.QApplication(sys.argv)
    with open(resource_path("stylesheet.qss")) as fh:
        text=fh.read()
    qss=platform_scaled_stylesheet(resource_path("stylesheet.qss"))
    app.setStyleSheet(qss)
    ex=OptWindow()
    sys.exit(app.exec_())


if __name__=="__main__":
    if getattr(sys, "frozen", False):
        mp.freeze_support()
    try:
        if sys.platform in ("darwin", "win32"):
            mp.set_start_method("spawn", force=True)
        else:
            mp.set_start_method("fork", force=True)
    except RuntimeError:
        pass

    main()
