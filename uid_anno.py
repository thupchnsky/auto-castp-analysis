import os
import sys
import json
import requests
from tqdm import tqdm


if __name__ == '__main__':
    # this is the prefix for UniProt ID search
    url_prefix = 'https://rest.uniprot.org/uniprotkb/search?query=accession%3A'
    with open('cluster-1-1_uniprot.txt') as f:
        uid_list = f.read().splitlines()

    uid_anno = {}
    total_anno_set = set()

    for uid in tqdm(uid_list):
        # print(f'Processing {uid_idx + 1} / {len(uid_list)}')
        # uid = 'A0A010YRR5'
        anno_list = []
        url = url_prefix + uid
        r = requests.get(url)
        if r.status_code == 200:
            data = r.content
            data = json.loads(data.decode('utf-8'))
            # check if the protein is still active
            if data['results'][0]['entryType'] != 'Inactive':
                # data now is a dict and here is the path to the proteinDescription
                protein_name = data['results'][0]['proteinDescription']
                protein_name_set = protein_name.keys()
                flag1 = 'submissionNames' in protein_name_set
                flag2 = 'recommendedName' in protein_name_set or 'alternativeNames' in protein_name_set
                # assert flag1 + flag2 == 1, uid
                if flag1:
                    for i in range(len(protein_name['submissionNames'])):
                        anno_list.append(protein_name['submissionNames'][i]['fullName']['value'])
                        total_anno_set.add(anno_list[-1])
                if flag2:
                    if 'recommendedName' in protein_name_set:
                        anno_list.append(protein_name['recommendedName']['fullName']['value'])
                        total_anno_set.add(anno_list[-1])
                    if 'alternativeNames' in protein_name_set:
                        for i in range(len(protein_name['alternativeNames'])):
                            anno_list.append(protein_name['alternativeNames'][i]['fullName']['value'])
                            total_anno_set.add(anno_list[-1])
            else:
                anno_list.append('Inactive')
                total_anno_set.add(anno_list[-1])
        else:
            print(f'{uid} with status code {r.status_code}')

        uid_anno[uid] = list(anno_list)

    # store the results
    with open('uid_anno.json', 'w') as fp:
        json.dump(uid_anno, fp)

    with open('total_anno_set.txt', 'w') as fp:
        for anno_name in total_anno_set:
            fp.write(anno_name + '\n')
