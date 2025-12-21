---
layout: default
title: How to use?
nav_order: 2
has_children: true
permalink: /using/
has_toc: false
---

{% include mathjax.html %}

# **Using the Program**

## **Table of Contents**

- [What IntegraTax does](#what-integratax-does)
- [Input files needed](#input-files-needed)
- [Clustering](#module-1)
  - [Mode 1: Own data](#mode-1)
  - [Mode 2: Own data + reference data](#mode-2)
  - [Mode 3: Clean-up messy data](#mode-3)
  - [Clustering output folder](#clustering-output-files)
- [Visualisation](#module-2)
  - [Visualisation functions](#visualisation-functions)
  - [Saving your progress](#saving-your-progress)
  - [Export formats](#export-formats-available)

---

## **What IntegraTax does**

Congratulations! You have accumulated your DNA sequences and are ready to analyse them!

IntegraTax has *two* modules:

**1.** **Clustering:** Groups your sequences into sets of speciemen based on pairwise distances hierarchically (single linkage/ Onjective clustering)
<br>
**2.** **Taxonomy:** For annotation of the clusters and specimens as a dendrogram (Cluster Fusion Diagram). 

First lets take the sequences through module 1 which gives you several options:

<img src="{{ '/assets/img/Overview.png' | relative_url }}" alt="Species Name File" width="700"><br>


---

## **Module 1: Objective clustering**

Typically IntegraTax Clustering module is run in Mode 1 (**one file**) or Mode 2 (**two input FASTA files**). Additionally an experimental Mode 3 is implemented to help you clean up a fasta file with non overlapping regions.

### Input files needed

#### 1. FASTA file(s)

- Keep sequence headers ≤ **150 characters**. FASTA file can be aligned or not unaligned. 

NOTE: If you have a 2nd fasta file with identified reference sequences for Mode 2 (e.g. from NCBI genbank or BOLD or sequences from other projects), 
IntegraTax can add those sequences to the clustering in [Step 3](#with-external-sequences). This file need not be aligned as this mode is always run with pairwise alignments

#### 2. Species name file (optional)

- Only required if you want **manual species name detection** instead of automatic extraction.
- Format: A `.csv` file containing species names that corresponds to your sequence headers.
**Example:** Column A is your sequence header, column B is your species name.

<center><img src="{{ '/assets/img/speciesnamefile.png' | relative_url }}" alt="Species Name File" width="400"></center><br>

---

## **Clustering**

#### **1. Open IntegraTax.** {#step-1}  
Haven’t installed it yet? [Go to the installation page]({{ "/installation/" | relative_url }}).
<br>

#### **2. Select the aim of your project** {#step-2}  
<img src="{{ '/assets/img/ModeSelection.gif' | relative_url }}" alt="Drag and Drop FASTA" width="700"><br>
<br>
IntegraTax offers you 3 modes. Click as needed
<br>

- [**Mode 1**] {#mode-1}: You have a set of sequences for specimens you want to study. The sequences are curated, i.e. you know they are overlapping and are of the target region
- [**Mode 2**]{#mode-2}: You have sequences for Mode 1, but also want to include some reference sequences that came from earlier studies (e.g. NCBI/BOLD)
- [**Mode 3**]{#mode-3} You are in an exploratory phase, have downloaded data from GenBank and want to clean it up to overlapping regions. You can clean up the data and cluster.

---

### **Mode 1** {#mode-1}

#### **Mode 1 Step 1. Drag your FASTA file into the box** {#mode-1-step-1}  
<img src="{{ '/assets/img/2ndFastaFilePrompt.png' | relative_url }}" alt="Alignment Prompt" width="500"> **NEEDS REPLACEMENT**
<br>

#### **Mode 1 Step 2. If you have aligned sequences, you will see a pop-up. Otherwise, proceed to [Mode 1 Step 3](#mode-1-step-3)** {#mode-1-step-2}
<br>
<img src="{{ '/assets/img/AlignmentPrompt1_cropped.png' | relative_url }}" alt="Alignment Prompt" width="500">   **NEEDS REPLACEMENT**
	- If your sequences are already aligned, select **Yes (Aligned)**.  
	- Otherwise, select **No (Pairwise)**.

#### **Mode 1 Step 3. Set up your clustering configuration** {#mode-1-step-3} 
<br>
<center><img src="{{ '/assets/img/SpeciesNameDetection_cropped.png' | relative_url }}" alt="Detect Species Name Option" width="400"></center><br>

- **Overlap length setting**
	- This is crucial because the software will alert if it finds too many short overlaps. It insists on having at least some minimum overlaps between fragments
- **Number of processors**
	- Number of processors used for distance calculations. This matters especially for large datasets.
- **Species name detection**
	- **Automatic (from FASTA headers):** Click **"Detect"**  
	- **Manual:** Click **"Add species name by file"** and select your [species name file](#2-species-name-file-optional)  
	- **No detection:** Click **"Do not detect"**
	
- Gap opening  and extension penalty (pairwise alignment mode only)
	- Allows you to modulate alignment parameters for pairwise alignment

#### **Mode 1 Step 4. Click “Cluster” to begin**. {#mode-1-step-4)
- After the clustering the dendrogram viewer `.html` will **open automatically** for visualisation (Module 2: Taxonomy)
- Refer to [Clustering Output files] #clustering-output-files for details of the outputs. 
<br>

---

### **Mode 2** {#mode-2}
This mode is for when you have 2 FASTA files (project and reference files)
<br>

#### **Mode 2 Step 1. Drag your Project FASTA file into the box** {#mode-2-step-1}  
You will notice an alert saying the top sequence is reference sequence. This is because we need to ensure that eventually overlapping regions make it to the dendrogram. The first sequence tunes the hit length parameter in the BLAST search done later. 
<img src="{{ '/assets/img/2ndFastaFilePrompt.png' | relative_url }}" alt="Alignment Prompt" width="500">  **NEEDS REPLACEMENT**
<br>

#### **Mode 2 Step 2. Drag your Reference FASTA file into the box** {#mode-2-step-2}  
<img src="{{ '/assets/img/2ndFastaFilePrompt.png' | relative_url }}" alt="Alignment Prompt" width="500">  **NEEDS REPLACEMENT**
<br>

#### **Mode 2 Step 3. Select the species you wish to include** {#mode-2-step-3}  
Unselect any unwanted species and click **Proceed**.  
<center><img src="{{ '/assets/img/ExternalSequenceSpeciesSelection.png' | relative_url }}" alt="Species Selection" width="500"> </center>

<br>

#### **Mode 2 Step 4. Select "BLAST based homology search"** {#mode-2-step-4}  
<center><img src="{{ '/assets/img/Externalsequences_alignmentmode.png' | relative_url }}" alt="Alignment mode" width="300"></center> 
<br>At this stage, ensure that the names of the folders where your 2nd fasta file is does 
not have spaces. For example, in the directory `/Users/Name/Desktop/GenBank Sequences/Mycetophilidae Sequences`, 
remove the space in `GenBank Sequences` and `Mycetophilidae Sequences` or replace them with another character. 
If there are spaces in the directory, the BLAST based homology search will **fail**!

Other homology search options can be found in the "Other options" button, click [**HERE**](#otheroptions) for more information, warnings, and instructions.

Click "Proceed" to continue.

<br>

#### **Mode 2 Step 5. Choose your settings for BLAST based homology search** {#mode-2-step-5}  
- Output prefix
- Threads
- Identity cutoff (%)
- Hit length cutoff (fraction)
- Number of hits

<center><img src="{{ '/assets/img/BlastSearchSettings.png' | relative_url }}" alt="BLAST search settings" width="400"></center>
Once done, click **Ok**.

<br>

#### **Mode 2 Step 6. Set the following alignment and clustering variables:** {#mode-2-step-6}
- Minimum overlap for clustering settings  
- Gap opening and extension penalty for alignment settings  
- Number of processors your computer can use  
- Species name detection options
<br>
<center><img src="{{ '/assets/img/Homologous-cluster-align-cropped.png' | relative_url }}" alt="Homologous align and cluster" width="400"></center>

<br>

#### **Mode 2 Step 7. Click “Cluster” to begin** {#mode-2-step-7}
- After the clustering the dendrogram viewer `.html` will **open automatically** for visualisation (Module 2: Taxonomy)
- Refer to [Clustering Output files] #clustering-output-files for details of the outputs. 
<br>

---

### **Mode 3** {#mode-3}
Mode 3 is a new "homology search" feature implemented in IntegraTax. It takes your first sequence in the fasta file, finds distances of this sequence from other files (Pass 1). Builds a distance profile and then implements KDE to smoothen the curve. It finds the antimode of this curve as a break point, and trims sequences falling within the distributio to overlapping areas. It then repeats this with 10 (default) sequences sampled across the distance profile of the first sequence to reduce biases introduced by your first reference (pass 2). 

#### **Mode 3 Step 1. Drag your FASTA file into the box** {#mode-3-step-1}  
Mode 3 is going to implement a homology search feature. This will use the first sequence of your file to define the reference and trim the longer or partially overlapping region to the region of interest.

<img src="{{ '/assets/img/2ndFastaFilePrompt.png' | relative_url }}" alt="Alignment Prompt" width="500">  **NEEDS REPLACEMENT**
<br>

#### **Mode 3 Step 2. On loading the first sequence ID will be printed** {#mode-3-step-2}  
Confirm based on the ID
<br>
#### **Mode 3 Step 3. Configure the search** {#mode-3-step-3}  
- Output prefix: This will print the output files with this prefix
- Max proportion of N: As homology searches are based on similarity, having too many Ns in the references can influence distance calculation. You can exclude the 
- Number of sequences for 2nd pass: See Mode 3 description. Number of sampled sequences.
- Min length fraction: Minimum length of overlap required to be considered a homologous fragment. 0.75 is default and this is because in fragmented landscape, this will ensure sufficient overlap between two partial sequences 
- Bandwidth: The distance distribution is smoothened by a Kernel Density Estimator implemented in SciPy, where the bandwidth is automatically selected using Silverman’s or Scott’s rule based on the data variance and sample size.
- KDE q_low: Lower quantile of the KDE-smoothed distance distribution used to restrict the analysis range and suppress extreme low-end outliers.
- KDE q_high: Upper quantile of the KDE-smoothed distance distribution used to restrict the analysis range and suppress extreme high-end outliers.
- Min prominence: Minimum required depth of a valley (relative to surrounding peaks) for it to be considered significant.
- Fixed threshold pass 1: By pass autodetection using fixed distance threshold (proportion)
- Fixed threshold pass 2: Same as above but for pass 2. (proportion)

<center><img src="{{ '/assets/img/homologysettings_new.png' | relative_url }}" alt="Find Homology settings" width="300">  </center>
Once done, click **Ok**.

<br>

#### **Mode 3 Step 4. Once homology search is done:** {#mode-3-step-4}

- Click **"Save log..."** to save the log.
  <br> 
  <center><img src="{{ '/assets/img/Homologysearchwindow_new.png' | relative_url }}" alt="Finish here message" width="500"></center>

- Click **"Finish here"** if you want to end the process and not continue with clustering. A pop-up reminds you to review results in the "Homology" folder of the output folder. **You will then be returned to the start page.**
  <br>
  <center><img src="{{ '/assets/img/Homologysearch_finishhere.png' | relative_url }}" alt="Finish here message" width="300"></center>

- Or click **"Proceed to clustering"** to move to the clustering step (Continue to **[Step 9](#noext-step-9)**).  
  <center>img src="{{ '/assets/img/Homologysearch_proceedtoclustering_new.png' | relative_url }}" alt="Proceed to clustering message" width="300"></center>

<br>

#### **Mode 2 Step 5. Set the following alignment and clustering variables:** {#mode-2-step-6}
- Minimum overlap for clustering settings  
- Gap opening and extension penalty for alignment settings  
- Number of processors your computer can use  
- Species name detection options
<br>
<center><img src="{{ '/assets/img/Homologous-cluster-align-cropped.png' | relative_url }}" alt="Homologous align and cluster" width="400"></center>

<br>

#### **Mode 2 Step 6. Click “Cluster” to begin** {#mode-2-step-7}
- After the clustering the dendrogram viewer `.html` will **open automatically** for visualisation (Module 2: Taxonomy)
- Refer to [Clustering Output files] #clustering-output-files for details of the outputs. 
<br>

---


### **Other Homology Search Options with identified reference sequences** {#otheroptions}
<center><img src="{{ '/assets/img/Externalsequences_alignmentmode_otheroptions.png' | relative_url }}" alt="Alignment mode" width="400">  </center>
Not the right option for you? Return to Step 6 [here](#ext-step-6)!

- **Find homology exhaustively**

	- **If you click "Find homology exhaustively"**, set the following variables: 
		- Output prefix: This will print the output files with this prefix
		- Max proportion of N: As homology searches are based on similarity, having too many Ns in the references can influence distance calculation. You can exclude the 
		- Number of sequences for 2nd pass: See Mode 3 description. Number of sampled sequences.
		- Min length fraction: Minimum length of overlap required to be considered a homologous fragment. 0.75 is default and this is because in fragmented landscape, this will ensure sufficient overlap between two partial sequences 
		- Bandwidth: The distance distribution is smoothened by a Kernel Density Estimator implemented in SciPy, where the bandwidth is automatically selected using Silverman’s or Scott’s rule based on the data variance and sample size.
		- KDE q_low: Lower quantile of the KDE-smoothed distance distribution used to restrict the analysis range and suppress extreme low-end outliers.
		- KDE q_high: Upper quantile of the KDE-smoothed distance distribution used to restrict the analysis range and suppress extreme high-end outliers.
		- Min prominence: Minimum required depth of a valley (relative to surrounding peaks) for it to be considered significant.
		- Fixed threshold pass 1: By pass autodetection using fixed distance threshold (proportion)
		- Fixed threshold pass 2: Same as above but for pass 2. (proportion)
			 
	<center> <img src="{{ '/assets/img/homologysettings_new.png' | relative_url }}" alt="Find Homology settings" width="300">  </center>
	 Once done, click **Ok**.
	<br>
	
	- **Once homology search is done:** 
	 
		- Click **"Save log..."** to save the log.
    <br>
	   <center><img src="{{ '/assets/img/Homologysearchwindow_new.png' | relative_url }}" alt="Finish here message" width="500"></center>
	 
		- Click **"Finish here"** to stop and review the "Homology" folder (you’ll return to the start page).
    <br>
	   <center><img src="{{ '/assets/img/Homologysearch_finishhere.png' | relative_url }}" alt="Finish here message" width="300"></center>
	 
		- Or **"Proceed to clustering"** (Continue to **[Step 8](#ext-step-8)**).
    <br>
	   <center><img src="{{ '/assets/img/Homologysearch_proceedtoclustering_new.png' | relative_url }}" alt="Proceed to clustering message" width="300"></center>
 	<br>
	
- **Assume homology with my sequences** — Go to **[Step 8](#ext-step-8)**  
Use this only when you are **absolutely certain** that your identified reference sequences are homologous to your project sequences!!


---

### **Clustering output files** {#clustering-output-files}

You will receive a nested folder (e.g. `IntegraTaxOut_20251007_101901`) in the same location as your input fasta file containing the following:

**FILES**
<br>**1.** `.itv` – used for dendrogram visualisation
<br>**2.** `IntegraTaxViz.html` – Visualisation of your dendrogram in `.html` format
<br>**3.** `bins.txt` – 
<br>**4.** `external.filtered.fa` (If you have identified reference sequences) – A fasta file containing your filtered identified reference sequences (after the blast homology search)
<br>**5.** `combined.fa` (If you have identified reference sequences) – A combined fasta file containing your project sequences and your filtered identified reference sequences (after the blast homology search)

**FOLDERS**
<br>**1.** `cluster` – Contains `iddict.txt`(mapping of IDs) and `_clusterlist`(Shows which sequences group into clusters across different distance thresholds)
<br>**2.** `pmatrix` – Pairwise matrix files
<br>**3.** `homology` (If you did a homology search without BLAST) – Contains the histogram and fasta files you should check before clustering
<br>**3.** `blast` (If you did a homology search with BLAST) – Contains the BLAST database created from your project sequences and results of the BLAST

---

## **Module 2 Taxonomy** {#module-2}

Once your clustering is complete, the `.html` dendrogram viewer opens automatically.  
To begin:
- Click **“Choose File”** and upload the **`.itv` file** from the clustering step.  

<img src="{{ '/assets/img/visualisationoverview.png' | relative_url }}" alt="Overview of Visualisation" width="700"> **NEEDS REPLACEMENT WITH SPART BUTTON**

---

### **Visualisation Functions** {#visualisation-functions}
Here are the main buttons on the top panel. Click below for more details:
- Choose File: To load the `.itv` for viewing
- Save: To save your visualisation as a `.itv` file for reloading in the future.
- [Export](#export)
- [Summary](#summary)
- [Color & Text](#colourtext)
- [Ruler: ON/OFF](#rulerscaling)
- [Log length: ON/OFF](#rulerscaling)
- [Instability](#instability)
- [Threshold](#threshold)

<br>

#### **<u>Export</u>** {#export}
Here are the following export formats you can choose:
- **SVG**  
  High-resolution dendrogram image for publications or sharing.

- **FASTA**  
  Information that you have assigned such as sex, verification status, contamination etc. 
  will be recorded in the sequence header.
  
- **Excel (LIT)**  
  Spreadsheet with:
  - Cluster information  
  - Haplotype statistics  
  - Assigned species names  
  - Sex / holotype indicators  
  - LIT status
  
- **SPART**  
  A standardised species delimitation output format.

<br>

#### **<u>Summary</u>** {#summary}
Here you can obtain some summary statistics for your sequences.

There will be a pop up asking if you if you would want to calculate the summary statistics for all percentage thresholds.
<center><img src="{{ '/assets/img/summarystats.png' | relative_url }}" alt="Summary stats" width="700"></center>
<br>If you do not have any species names assigned to the clusters, it will only show the graph of "Clusters" against "Threshold".
If you do have species names, it will also calculate the match ratio (Species congruence) and specimen congruence.

<br>
<center><img src="{{ '/assets/img/meier-etal-2025_figure1.png' | relative_url }}" alt="Match ratio and specimen congruence figure" width="500"></center>
<br>
<br>
**Match ratio ([Ahrens et al. 2016](https://doi.org/10.1093/sysbio/syw002))**

$$
\text{Match ratio} \;=\; \frac{2 \times N_{\text{congruent}}}{N_{\text{morpho}} + N_{\text{method}}}
$$

{% raw %}
where $N_{\text{congruent}}$ is the number of clusters congruent between the method and morphology, $N_{\text{morpho}}$ is the number of morphospecies, $N_{\text{method}}$ is the number of method-based clusters.
{% endraw %}
<br>
**Specimen congruence ([Meier et al. 2025](https://doi.org/10.1146/annurev-ento-040124-014001); Derived from [Yeo et al. 2020](https://doi.org/10.1093/sysbio/syaa014))**

$$
\text{Specimen congruence} \;=\;
\frac{\#\text{congruent specimens}}{\#\text{specimens total}}
$$

<br>

#### **<u>Color & Text</u>** {#colourtext}
Cluster and node colours in the dendrogram are based on the [**LIT workflow**]({{ "/lit/" | relative_url }}) by default.

You can edit the colours of the nodes, cluster(subtree) branches, and text here:
- **Subtree colour** (*PI/nonPI* / *Binomial name* / *None*)
- **Terminal node colour** (*Binomial name* / *Cluster* / *Haplotype* / *LIT selections* / *None*)
- **Node colour** (*PI/nonPI* / *Binomial name* / *None*):
- **Text colour** (*Binomial name* / *Cluster* / *Haplotype* / *LIT selections* / *None*)


You can change the text settings here:
- **Node text**: Change the numbers beside the nodes to fusepoints, MaxP(Maximum Pairwise Distance), or Node ID
- **Terminal text length**: Are your sequence headers too long? You can truncate it to your desired character length. 
Hovering your cursor over the headers will reveal the entire header.

<br>

#### **<u>Ruler and branch length scaling controls</u>** {#rulerscaling}
Adjust the dendrogram’s scale and view thresholds for better interpretation of cluster distances.
- **Ruler: ON/OFF** — shows or hides pairwise distance threshold scale
- **Log length: ON/OFF** — toggle logarithmic branch length view

<br>

#### **<u>SPART visualization</u>** {#spart}
You can get SPART outputs from other species delimitation approaches using SPART explorer: For example use [SPART explorer](https://spartexplorer.mnhn.fr/) to get it for ASAP/ABGD 
<br>
- **Load** the SPART file
- **Panel:** You can see the panel on the right that summarizes multiple delimtation schemes. 
	- It first builds a unified species delimitation where any scheme in any delimtiation gets a unique identifier. 
	- This is then used to show consistancy across partitions.
- The tool tip can be used to identify the cluster. Split clusters are shown with dashed boxes

<br>

#### **<u>Instability</u>** {#instability}
Adjust your Instability maximum and minimum percentages and maximum pairwise distance (Max P) here.
You can also turn the instability zone (light green background of the dendrogram) on or off.
For more information about Max P and Instability, click [**here**]({{ "/lit/" | relative_url }})!

<br>

#### **<u>Threshold</u>** {#threshold}
You can adjust the clustering threshold to check the number of corresponding clusters. You can 
also collapse part of the dendrogram at a specific threshold of your choosing.

<br>

#### **<u>Right-click options</u>** {#rightclick}
The right-click menu allows you to set verification statuses, assign metadata, 
and perform various actions on individual specimens or entire clusters.

**Right-click on a specimen (terminal) node** to:
- **Set as Verified** – Mark the specimen as checked and correct
- **Cannot be verified** – Missing or damaged specimen
- **Set as Contamination** – Mark as contamination if the specimen clearly belongs to a different species
- **Set as Male** – Indicate specimen is male
- **Set as Female** – Indicate specimen is female
- **Set as Holotype** – Mark the specimen as the holotype
- **Set as Slide Mounted Specimen** – Indicate the specimen is slide-mounted
- **Accept code as species name** – Use the specimen code as its species name
- **Edit/Enter species name** – Assign a user-defined species name
- **Copy FASTA sequence** – Copies the sequence header and sequence into clipboard
- **Copy Sequence / Search online** – Copies the sequence header and sequence and opens search tools for:
  - Barcode of Life Data Systems (BOLD)
  - NCBI (National Center for Biotechnology Information) GenBank
  - Global Biodiversity Information Facility (GBIF)
- **Add notes** – Add any information tagged to the node
- **Freeze / Unfreeze** – Prevent or allow further changes to the node
- **Undo** – Revert the most recent change done to the node

**Right-click on a cluster (internal) node** to:
- **Export FASTA** – Download all sequences in the cluster as a `.fasta` file
- **Accept lowest code as species name** – Use the lowest specimen code of the cluster as its species name
- **Enter species name** – Assign a user-defined species name
- **Collapse / Expand subtree** – Collapse the cluster(subtree) into a single node or to show all specimens in the cluster
- **Copy sequence / Search Online** – Copies all headers and sequences of the cluster and opens search tools for:
  - Barcode of Life Data Systems (BOLD)
  - NCBI (National Center for Biotechnology Information) GenBank
  - Global Biodiversity Information Facility (GBIF)
- **Add notes** – Add any information tagged to the node
- **Freeze / Unfreeze** – Prevent or allow further changes to the node
- **Undo** – Revert the most recent change done to the node

If the specimen (terminal) node and cluster (internal) node is shared, **[left-click]({{ "/faq/#visualisation" | relative_url }})**
the node to switch between both right-click options.

---

### **Saving your progress** {#saving-your-progress}

Click the **"Save"** button to export a `.itv` save file with your edits:

- Verification status (e.g. verified, cannot be verified)
- Assigned specimen information (e.g. species names, sex, condition, type status, notes)

To resume your work, upload the `.itv` using the **“Choose File”** button.

---

### **Export formats available** {#export-formats-available}

- **FASTA**  
  The labels that you set (Verification statuses, sex, holotype, contamination, slide-mounted specimens) will be noted in your sequence header. 
  However, the notes from "Add notes" will not be in your sequence header.

- **SVG**  
  High-resolution dendrogram image for publications or sharing. Similarly, labels that 
  you have set will be shown but notes from "add notes" will not be reflected.

- **SPART**  
  A standardised species delimitation output format.

- **Excel (LIT)**  
  Spreadsheet with 9 columns:
  - **ID:** Sequence header
  - **SpName:** Corresponding species name that IntegraTax has detected or you have assigned  
  - **Haplotype:** The name of the haplotype cluster the particular specimen is in based on the "lowest" sequence name 
  - **LIT selection:** Specimens that IntegraTax suggests for checking based on [LIT]({{ "/lit/#what-is-lit" | relative_url }})
  - **Cluster:** Cluster number based on your chosen [percentage threshold](#threshold)
  - **Sex:** Male or female based on your input from the [right-click options](#rightclick)
  - **Holotype:** Holotype or not(blank) based on your input from the [right-click options](#rightclick)
  - **Status:** "Verified", "Cannot be verified", "Contamination", "Slide Mounted" or blank based on your input from the [right-click options](#rightclick)
  - **Notes:** Contains any notes you have added from the [right-click options](#rightclick)
