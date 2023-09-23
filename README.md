# castp-Script

## Update

The script `auto_castp` now fully supports headless Linux machines without GUI. And geckodriver is no longer needed. The workflow of this script is the following:

- Download pdb files from AlphaFold data bank directly

- Upload pdb file to castp site automatically

- Get results from castp site automatically

- Extract the poc table from the castp results and save to excel files

**Note that not all Mega-1-1 ids are valid for AlphaFold (and UniProt). Invalid ids are skipped and recorded in `failed.txt`.**

## Intro

A Python script to run [CASTp](http://sts.bioe.uic.edu/castp/calculation.html) code from the command line.

CASTp (expanded as Computed Atlas of Surface Topography of Proteins) is  an online tool used for finding surface pockets and internal cavities in proteins which are possibly active sites for ligand binding.

**This script uses selenium and geckodriver to load the webpage and parse it.**

**The script will take a few seconds to run. An initial time delay of 10 seconds is added to avoid sending frequent requests to the website.**

**Currently, the script only works for machines with GUI.**

## Instructions to Setup the script

- Clone this repository.
- Install `requirements.txt` using 

    ```pip install -r requirements.txt```
  
<!---
- Download geckodriver from the [github link](https://github.com/mozilla/geckodriver/releases) suitable for your OS.

- **Linux** users should isntall geckodriver in `/usr/local/bin`or in `/usr/bin`.

- **Windows** users should install firefox browser first at default location : ```C:\Program Files\Mozilla Firefox```
- Then install geckodriver at the location : ```C:\WebDrivers```
-->

- Change User-Agent from `headers`:
User_Agent_Info = 'Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0'`
change this with the header for your machine. For that, goto https://myhttpheader.com/. Copy User-Agent value from there and paste it here. 

## Instructions to run the script

- For help text, run :

    ```python castp.py -h```

- Input the protein file in pdb format as given below:

    ```python castp.py -p <<<protein name>>>```

- If you wish to mention radius probe, use `-r` or `--radius` arguement. Default value is _1.4_.
- If your network is slow, please set wait time to desired time. Use the tag `--wait` or `-w` with time in seconds. Default value is _10_.

- If the code run succeeds, output files will be generated in the folder.

- Output consists of:
    - Area and volume information.
    - Image of protein structure
    - Active sites and their information.
    - Protein sequence.


## References

-  Tian et al., Nucleic Acids Res. 2018. PMID: 29860391 DOI: 10.1093/nar/gky473. 
-  Original repo: https://github.com/athulvis/castp-Script






