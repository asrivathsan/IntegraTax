---
layout: default
title: How to use?
nav_order: 2
has_children: true
permalink: /using/
has_toc: false
---

{% include mathjax.html %}

# **Using the Programme**

## **Table of Contents**

- [What IntegraTax does](#what-integratax-does)
- [Input files needed](#input-files-needed)
- [Clustering](#clustering)
  - [Without external sequences](#without-external-sequences)
    - [Aligned sequences](#noext-step-5)
    - [Unaligned sequences](#noext-step-6)
  - [With external sequences](#with-external-sequences)
    - [Alignment modes](#ext-step-6)
    - [BLAST search](#ext-step-9)
  - [Clustering output folder](#clustering-output-files)
- [Visualisation](#visualisation)
  - [Visualisation functions](#visualisation-functions)
  - [Saving your progress](#saving-your-progress)
  - [Export formats](#export-formats-available)

---

## **What IntegraTax does**

Congratulations! You have accumulated your DNA sequences and are ready to analyse them!

IntegraTax has *two* main functions:

**1.** **Clustering:** Groups your sequences into molecular Operational Taxonomic Units (mOTUs; putative species) based on pairwise distances.  
**2.** **Visualization:** Displays the clusters and specimens as a dendrogram (Cluster Fusion Diagram).

---

## **Input files needed**

IntegraTax requires at most **two input files**:

### 1. FASTA file(s)

- Keep sequence headers ≤ **150 characters**.

NOTE: If you have fasta sequences that are separate from your project (e.g. from NCBI genbank or BOLD or sequences from other projects), 
these files are called **external sequences** and IntegraTax can add those sequences to the clustering.

### 2. Species name file (optional)

- Only required if you want **manual species name detection** instead of automatic extraction.
- Format: A `.csv` file containing species names that corresponds to your sequence headers.
**Example:** Column A is your sequence header, column B is your species name.

<img src="/assets/img/speciesnamefile.png" alt="Species Name File" width="700"><br>

---

## **Clustering**

#### **1. Open IntegraTax.** {#step-1}  
Haven’t installed it yet? [Go to the installation page](/installation/).
<br>

#### **2. Drag and drop your FASTA file into the IntegraTax GUI.** {#step-2}  
<img src="/assets/img/DragAndDrop.gif" alt="Drag and Drop FASTA" width="700"><br>
<br>

#### **3. Depending on your data, click the following for the next instructions:** {#step-3}
- [Without external sequences](#without-external-sequences)
- [With external sequences](#with-external-sequences)
<br>

---

### **Without external sequences** {#without-external-sequences}

#### **4. Click "no"** {#noext-step-4}  
<img src="/assets/img/ExternalSequencesPrompt_no_cropped.png" alt="Alignment Prompt" width="500"> 
<br>

#### **5. If you have aligned sequences, you will see this pop-up. Otherwise, proceed to [Step 6](#noext-step-6)** {#noext-step-5}  
<img src="/assets/img/AlignmentPrompt1_cropped.png" alt="Alignment Prompt" width="500">  
- If your sequences are already aligned, select **Yes (Aligned)** and proceed to **[Step 10](#noext-step-10)**.  
- Otherwise, select **No (Pairwise)** and proceed to **[Step 6](#noext-step-6)**.
<br>

#### **6. Select pairwise alignment mode** {#noext-step-6}  
<img src="/assets/img/homologousornot.png" alt="Homologous Unaligned" width="700">  
- **Homologous sequences** — Go to **[Step 9](#noext-step-9)**. Use this if all sequences represent the **same gene region** with minor start/end variation (typical *COI* barcode datasets).  
- **Find homology** — Go to **[Step 7](#noext-step-7)**. Use this for **non-overlapping fragments** or highly variable lengths/coverage.
<br>

#### **7. If you click "Find homology"**, set the following variables: {#noext-step-7}
- Output prefix  
- Min coverage  
- Max N fraction  
- Rep count  
- Min length frac  
- KDE grid  
- KDE bandwidth  
- KDE q_low  
- KDE min prominence  

<img src="/assets/img/homologysettings.png" alt="Find Homology settings" width="500">  
Once done, click **Ok**.

<br>

#### **8. Once homology search is done:** {#noext-step-8}

- Click **"Save log..."** to save the log.  
  <img src="/assets/img/Homologysearchwindow.png" alt="Finish here message" width="700">

- Click **"Finish here"** if you want to end the process and not continue with clustering. A pop-up reminds you to review results in the "Homology" folder of the output folder. **You will then be returned to the start page.**  
  <img src="/assets/img/Homologysearch_finishhere.png" alt="Finish here message" width="500">

- Or click **"Proceed to clustering"** to move to the clustering step (Continue to **[Step 9](#noext-step-9)**).  
  <img src="/assets/img/Homologysearch_proceedtoclustering.png" alt="Proceed to clustering message" width="500">

<br>

#### **9. If you clicked "Homologous sequences" or completed homology search, set:** {#noext-step-9}
- Minimum overlap for clustering settings  
- Gap opening and extension penalty for alignment settings  
- Number of processors your computer can use  
- Species name detection options

<img src="/assets/img/Homologous-cluster-align-cropped.png" alt="Homologous align and cluster" width="700">  
Once done, go to **[Step 11](#noext-step-11)**.

<br>

#### **10. Choose species name detection mode** {#noext-step-10}  
<img src="/assets/img/SpeciesNameDetection_cropped.png" alt="Detect Species Name Option" width="700"><br>
- **Automatic (from FASTA headers):** Click **"Detect"**  
- **Manual:** Click **"Add species name by file"** and select your [species name file](#2-species-name-file-optional)  
- **No detection:** Click **"Do not detect"**

<br>

#### **11. Click “Cluster” to begin** {#noext-step-11}

<br>

#### **12. After clustering completes** {#noext-step-12}  
the dendrogram viewer `.html` will **open automatically** for visualisation.  

<br>

---

### **With external sequences** {#with-external-sequences}

#### **4. Click "Select"** {#ext-step-4}  
<img src="/assets/img/ExternalSequencesPrompt_select_cropped.png" alt="Alignment Prompt" width="500"> 
<br>

#### **5. Select the species you wish to include** {#ext-step-5}  
Unselect any unwanted species and click **Proceed**.  
<img src="/assets/img/ExternalSequenceSpeciesSelection.png" alt="Species Selection" width="700"> 

<br>

#### **6. Select "BLAST based homology search"** {#ext-step-6}  
<img src="/assets/img/Externalsequences_alignmentmode.png" alt="Alignment mode" width="500"> 
<br>At this stage, ensure that the names of the folders where your external sequences are does 
not have spaces. For example, in the directory `/Users/Name/Desktop/GenBank Sequences/Mycetophilidae Sequences`, 
remove the space in `GenBank Sequences` and `Mycetophilidae Sequences` or replace them with another character. 
If there are spaces in the directory, the BLAST based homology search will **fail**!

Other homology search options can be found in the "Other options" button, click [**HERE**](#otheroptions) for more information, warnings, and instructions.

Click "Proceed" to continue.

<br>

#### **7. Choose your settings for BLAST based homology search** {#ext-step-7}  
- Output prefix
- Threads
- Identity cutoff (%)
- Hit length cutoff (fraction)
- Number of hits

<img src="/assets/img/BlastSearchSettings.png" alt="BLAST search settings" width="700">
Once done, click **Ok**.

<br>

#### **8. Set the following alignment and clustering variables:** {#ext-step-8}
- Minimum overlap for clustering settings  
- Gap opening and extension penalty for alignment settings  
- Number of processors your computer can use  
- Species name detection options

<img src="/assets/img/Homologous-cluster-align-cropped.png" alt="Homologous align and cluster" width="700">

<br>

#### **9. Click “Cluster” to begin** {#ext-step-9}

<br>

#### **10. After clustering completes** {#ext-step-10}  
the dendrogram viewer `.html` will **open automatically** for visualisation.  

---

### **Other Homology Search Options with external sequences** {#otheroptions}
<img src="/assets/img/Externalsequences_alignmentmode_otheroptions.png" alt="Alignment mode" width="500">  
Not the right option for you? Return to Step 6 [here](#ext-step-6)!

- **Find homology exhaustively**

	- **If you click "Find homology exhaustively"**, set the following variables: 
		- Output prefix  
		- Min coverage  
		- Max N fraction  
		- Rep count  
		- Min length frac  
		- KDE grid  
		- KDE bandwidth  
		- KDE q_low  
		- KDE min prominence  
	 
	 <img src="/assets/img/homologysettings.png" alt="Find Homology settings" width="500">  
	 Once done, click **Ok**.
	<br>
	
	- **Once homology search is done:** 
	 
		- Click **"Save log..."** to save the log.  
	   <img src="/assets/img/Homologysearchwindow.png" alt="Finish here message" width="700">
	 
		- Click **"Finish here"** to stop and review the "Homology" folder (you’ll return to the start page).  
	   <img src="/assets/img/Homologysearch_finishhere.png" alt="Finish here message" width="500">
	 
		- Or **"Proceed to clustering"** (Continue to **[Step 8](#ext-step-8)**).  
	   <img src="/assets/img/Homologysearch_proceedtoclustering.png" alt="Proceed to clustering message" width="500">
 	<br>
	
- **Assume homology with my sequences** — Go to **[Step 8](#ext-step-8)**  
Use this only when you are **absolutely certain** that your external sequences are homologous to your project sequences!!


---

### **Clustering output files** {#clustering-output-files}

You will receive a nested folder (e.g. `IntegraTaxOut_20251007_101901`) in the same location as your input fasta file containing the following:

**FILES**
<br>**1.** `.itv` – used for dendrogram visualisation
<br>**2.** `IntegraTaxViz.html` – Visualisation of your dendrogram in `.html` format
<br>**3.** `bins.txt` – 
<br>**4.** `external.filtered.fa` (If you have external sequences) – A fasta file containing your filtered external sequences (after the blast homology search)
<br>**5.** `combined.fa` (If you have external sequences) – A combined fasta file containing your project sequences and your filtered external sequences (after the blast homology search)

**FOLDERS**
<br>**1.** `cluster` – Contains `iddict.txt`(mapping of IDs) and `_clusterlist`(Shows which sequences group into clusters across different distance thresholds)
<br>**2.** `pmatrix` – Pairwise matrix files
<br>**3.** `homology` (If you did a homology search without BLAST) – Contains the histogram and fasta files you should check before clustering
<br>**3.** `blast` (If you did a homology search with BLAST) – Contains the BLAST database created from your project sequences and results of the BLAST

---

## **Visualisation** {#visualisation}

Once your clustering is complete, the `.html` dendrogram viewer opens automatically.  
To begin:
- Click **“Choose File”** and upload the **`.itv` file** from the clustering step.  

<img src="/assets/img/visualisationoverview.png" alt="Overview of Visualisation" width="700">

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
<img src="/assets/img/summarystats.png" alt="Summary stats" width="700">
<br>If you do not have any species names assigned to the clusters, it will only show the graph of "Clusters" against "Threshold".
If you do have species names, it will also calculate the match ratio (Species congruence) and specimen congruence.

<br>
<img src="/assets/img/meier-etal-2025_figure1.png" alt="Match ratio and specimen congruence figure" width="700">
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
Cluster and node colours in the dendrogram are based on the [**LIT workflow**](/lit/) by default.

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

#### **<u>Instability</u>** {#instability}
Adjust your Instability maximum and minimum percentages and maximum pairwise distance (Max P) here.
You can also turn the instability zone (light green background of the dendrogram) on or off.
For more information about Max P and Instability, click [**here**](/lit/)!

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

If the specimen (terminal) node and cluster (internal) node is shared, **[left-click](/faq/#visualisation)**
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
  - **LIT selection:** Specimens that IntegraTax suggests for checking based on [LIT](/lit/#what-is-lit)
  - **Cluster:** Cluster number based on your chosen [percentage threshold](#threshold)
  - **Sex:** Male or female based on your input from the [right-click options](#rightclick)
  - **Holotype:** Holotype or not(blank) based on your input from the [right-click options](#rightclick)
  - **Status:** "Verified", "Cannot be verified", "Contamination", "Slide Mounted" or blank based on your input from the [right-click options](#rightclick)
  - **Notes:** Contains any notes you have added from the [right-click options](#rightclick)
