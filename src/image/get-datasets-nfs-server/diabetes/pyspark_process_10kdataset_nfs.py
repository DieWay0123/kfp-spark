import os
import shutil
from dotenv import load_dotenv, dotenv_values

config = dotenv_values(".env")

nfs_server = config["NFS_SERVER"]
mount_point = config["MOUNT_POINT"]
pwd = config["PASSWORD"]

# mount nfs
if not os.path.exists(mount_point):
    os.makedirs(mount_point)

os.system(f"echo {pwd} | sudo -S mount -t nfs {nfs_server} {mount_point}")

# copy file
source_file = config["SOURCE_FILE"]
destination_file = config["DESTINATION_FILE"]

# 複製文件
while not os.path.exists(source_file):
    print(f"file {source_file} not found")

shutil.copyfile(source_file, destination_file)


os.system(f"sudo umount {mount_point}")
#os.system(f"chmod -R 777 {destination_file}")
os.system(f"echo copy datasets from nfs-servre DONE!")