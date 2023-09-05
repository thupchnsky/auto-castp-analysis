import requests
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from biopandas.pdb import PandasPdb
import pandas as pd
import argparse
import sys
import os
import base64


# This needs to be changed for different machines
# This info can be obtained by visiting https://myhttpheader.com/
User_Agent_Info = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/109.0'


if __name__ == '__main__':
    parser = argparse.ArgumentParser("Automatic castp analysis, parsing, and saving")
    parser.add_argument("-p", "--pdb", required=True, type=str, help='Protein file name in pdb format.')
    parser.add_argument("-r", "--radius", type=str, default='1.4',
                        help='Value for radius probe, between 0.0 and 10.0. Default is 1.4.')
    parser.add_argument("-w", "--wait", type=int, default=10,
                        help='Wait time to load the page. Default is 10. Use 20 or more if internet is slow.')
    parser.add_argument("-o", "--output", type=str, default='results',
                        help='Output folder.')
    args = parser.parse_args()

    file = open(args.pdb, 'rb')

    url = 'http://sts.bioe.uic.edu/castp/submit_calc.php'
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
        'file': (args.pdb, file, 'application/x-aportisdoc'),
    }
    data = {
        'probe': args.radius,
        'email': 'null'
    }

    response = requests.post(url, headers=headers, data=data, files=files)
    job_id = str(response.text)

    print(f'CASTp job id: {job_id}')
    print(f'The results can also be found at http://sts.bioe.uic.edu/castp/index.html?{job_id}')
    file.close()
    time.sleep(args.wait)

    # choose whatever browser you like
    # for now the script only works for machines that can open the browser GUI
    # TODO: make the script compatible with headless machines
    # opts = FirefoxOptions()
    # opts.add_argument("--headless")
    # driver = webdriver.Firefox(options=opts)

    driver = webdriver.Firefox()

    if not driver:
        print("Webdriver not found. **Program will stop**")
        sys.exit()

    # this is the url to retrieve the results
    url = "http://sts.bioe.uic.edu/castp/index.html?" + job_id

    driver.get(url)

    # wait until the results are ready
    WebDriverWait(driver, args.wait).until(lambda d: d.execute_script("return document.readyState") == "complete")
    WebDriverWait(driver, args.wait).until(EC.presence_of_element_located((By.XPATH, '//*[@id="poc_table"]')))
    time.sleep(args.wait)

    if '-F1-model' in args.pdb:
        # the pdb file is from AlphaFold
        sub_folder = args.pdb[: args.pdb.find('-F1-model')]
    else:
        sub_folder = args.pdb.split('.')[0]

    if not os.path.exists(os.path.join(args.output, sub_folder)):
        # if the demo_folder directory is not present
        # then create it.
        os.makedirs(os.path.join(args.output, sub_folder))

    # save the page source for later use
    with open(os.path.join(args.output, sub_folder, f'{sub_folder}-castp.html'), 'w', encoding='utf-8') as f:
        f.write(driver.page_source)

    # save the plot
    canvas = driver.find_element(By.CSS_SELECTOR, "#undefined")
    canvas_base64 = driver.execute_script("return arguments[0].toDataURL('image/png').substring(21);", canvas)
    canvas_png = base64.b64decode(canvas_base64)
    with open(os.path.join(args.output, sub_folder, f'{sub_folder}.png'), 'wb') as f:
        f.write(canvas_png)

    # save the AA sequence
    css_txt = driver.find_element(By.CSS_SELECTOR, ".seqpanel")
    with open(os.path.join(args.output, sub_folder, f'{sub_folder}-sequence.txt'), 'w') as f:
        f.write(str(css_txt.text))

    # parse the table
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    table = soup.find_all('table', {'id': 'atom_table'})
    tr = table[0].find_all("tr")
    data = []
    for elem in tr[1:]:
        sub_data = []
        for sub_e in elem:
            try:
                if sub_e.get_text() != "\n":
                    sub_data.append(sub_e.get_text())
            except:
                continue
            data.append(sub_data)

    table2 = soup.find_all('table', {'id': 'poc_table'})
    tr2 = table2[0].find_all("tr")
    data2 = []
    for elem in tr2:
        elem_list = elem.text.split('\n')
        sub_data2 = []
        for elem_sub in elem_list:
            if len(elem_sub) == 0 or 'help' in elem_sub:
                continue
            else:
                sub_data2.append(elem_sub)
        data2.append(' | '.join(sub_data2))

    # for ele in tr2[1:]:
    #     sub_data2 = []
    #     for sub_e2 in ele:
    #         try:
    #             if sub_e2.get_text() != "\n":
    #                 sub_data2.append(sub_e2.get_text())
    #         except:
    #             continue
    #         data2.append(list(set(sub_data2)))

    driver.close()

    # save the area and volume
    with open(os.path.join(args.output, sub_folder, f'{sub_folder}-area-vol.txt'), 'w') as f:
        f.write('\n'.join(data2))

    df_csv = pd.DataFrame(data)
    df_csv.drop_duplicates(inplace=True)
    df_csv.reset_index(drop=True, inplace=True)
    ppdb_df = PandasPdb().read_pdb(args.pdb)
    df2 = ppdb_df.df['ATOM']
    df_csv.columns = ["PocID", "Chain",	"residue_number", "residue_name", "atom_name"]
    dtype_dict = {"PocID": "int64", "Chain": str, "residue_number": "int64", "residue_name": str, "atom_name": str}
    df_csv = df_csv.astype(dtype_dict)
    output = pd.merge(df2, df_csv, on=["residue_number", "residue_name", "atom_name"], how='inner')
    new_out = output[["residue_number", "residue_name", "atom_name", "x_coord", "y_coord", "z_coord"]]
    new_out.to_excel(os.path.join(args.output, sub_folder, f'{sub_folder}-cavity.xlsx'))

    print(f"files created successfully for {args.pdb}.")
