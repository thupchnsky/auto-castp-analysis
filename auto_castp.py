import requests
import argparse
import time
import sys
import os
import pandas as pd
from tqdm import tqdm

# This needs to be changed for different machines
# This info can be obtained by visiting https://myhttpheader.com/
User_Agent_Info = 'Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0'


def process(line):
    """
    Turn one poc line to a list
    :param line: One line from poc file
    :return: ['Chain', 'residue_number', 'residue_name', 'atom_name', 'x_coord', 'y_coord', 'z_coord']
    """
    info_list = line.split()
    if info_list[-2] == '1':
        return [info_list[4], int(info_list[5]), info_list[3], info_list[2], float(info_list[6]), float(info_list[7]), float(info_list[8])]
    else:
        return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser("automatic castp analysis, parsing, and saving")
    parser.add_argument("-r", "--radius", type=str, default='1.4',
                        help='value for radius probe, between 0.0 and 10.0. Default is 1.4.')
    parser.add_argument("-w", "--wait", type=int, default=10,
                        help='wait time to load the page. Default is 10. Use 20 or more if internet is slow.')
    parser.add_argument("-i", "--input", type=str, default='cluster-1-1_uniprot.txt',
                        help='input id list')
    parser.add_argument("-o", "--output", type=str, default='results',
                        help='output folder.')
    args = parser.parse_args()

    with open(args.input, 'r') as fr:
        id_list = fr.read().splitlines()

    failed_list = []

    for uniprot_id in tqdm(id_list):
        sub_folder = os.path.join(args.output, uniprot_id)
        if not os.path.exists(sub_folder):
            os.makedirs(sub_folder)

        pdb_url = f'https://alphafold.ebi.ac.uk/files/AF-{uniprot_id}-F1-model_v4.pdb'
        pdb_path = os.path.join(sub_folder, f'{uniprot_id}.pdb')
        os.system(f'curl -o {pdb_path} {pdb_url}')
        
        # check if the pdb file is not empty
        with open(pdb_path, 'r') as fr:
            first_line = fr.readline()
        if 'Error' in first_line:
            failed_list.append(uniprot_id)
            continue
        
        # submit the castp job
        try:
            
            file = open(pdb_path, 'rb')
            castp_url = 'http://sts.bioe.uic.edu/castp/submit_calc.php'
            headers = {
                'User-Agent': User_Agent_Info,
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'X-Requested-With': 'XMLHttpRequest',
                'Origin': 'http://sts.bioe.uic.edu',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Referer': 'http://sts.bioe.uic.edu/castp/calculation.html'
            }
            files = {
                'file': (pdb_path, file, 'application/x-aportisdoc'),
            }
            data = {
                'probe': args.radius,
                'email': 'null'
            }

            response = requests.post(castp_url, headers=headers, data=data, files=files)
            job_id = str(response.text)
            file.close()
            time.sleep(args.wait)

            # download the castp analysis results
            poc_url = f'http://sts.bioe.uic.edu/castp/data/tmppdb/{job_id}/processed/{job_id}.zip'
            poc_path = os.path.join(sub_folder, f'{job_id}.zip')
            os.system(f'curl -o {poc_path} {poc_url}')
            # unzip the file
            poc_folder = os.path.join(sub_folder, job_id)
            os.system(f'unzip {poc_path} -d {poc_folder}')

            # after the files have been unzipped
            with open(os.path.join(poc_folder, f'{job_id}.poc'), 'r') as fr:
                lines = fr.read().splitlines()

            d = {'Chain': [], 'residue_number': [], 'residue_name': [], 'atom_name': [], 'x_coord': [], 'y_coord': [], 'z_coord': []}
            df = pd.DataFrame(data=d)
            for line in lines:
                line_data = process(line)
                if line_data:
                    df.loc[len(df.index)] = line_data

            df.to_excel(os.path.join(sub_folder, 'castp-cavity.xlsx'))
            
        except:
            
            failed_list.append(uniprot_id)

    print('Number of failed proteins', len(failed_list))
    with open(os.path.join(args.output, 'failed.txt'), 'w') as fw:
        for uniprot_id in failed_list:
            fw.write(uniprot_id + '\n')
    