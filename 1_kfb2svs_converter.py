import os
import subprocess
from time import time
 
def main():
    src_folder_name = './data_example/kfb'
    des_folder_name = './data_example/svs'
    level = 9
 
    exe_path = r'./KFB.Tif.SVS.2.0/KFB转Tif或SVS工具2.0/x86/KFbioConverter.exe'
    if not os.path.exists(exe_path):
        raise FileNotFoundError('Could not find convert library.')
 
    if int(level) < 2 or int(level) > 9:
        raise AttributeError('NOTE: 2 < [level] <= 9')
 
    pwd = os.popen('chdir').read().strip()
    full_path = os.path.join(pwd, src_folder_name)
    dest_path = os.path.join(pwd, des_folder_name)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f'could not get into dir {src_folder_name}')
    if not os.path.exists(dest_path):
        os.makedirs(dest_path)
 
    kfb_list = os.popen(f'dir {full_path}').read().split('\n')
    kfb_list = [f for f in os.listdir(full_path) if f.lower().endswith('.kfb')]
 
    print(f'Found {len(kfb_list)} slides, transfering to svs format ...')
    for elem in kfb_list:
        st = time()
        kfb_elem_path = os.path.join(full_path, elem)
        print(kfb_elem_path)
        svs_dest_path = os.path.join(dest_path, elem.replace('.kfb', '.svs'))
        command = f'"{exe_path}" "{kfb_elem_path}" "{svs_dest_path}" {level}'
        print(f'Processing {elem} ...')
        p = subprocess.Popen(command, shell=True)
        p.wait()
        print(f'\nFinished {elem}, time: {time() - st}s ...')
 
 
if __name__ == "__main__":
    main()
