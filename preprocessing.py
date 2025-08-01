from Utilis.utilis import generate_pages_range
import random
import os
import shutil
folder_path = input("Enter the folder path: ")
number_of_files = input("Enter the number of files to process: ")
if os.path.exists(os.path.join(folder_path, "final_selected_folder")):
    print("The folder 'final_selected_folder' already exists. automatically deleting it.")
    shutil.rmtree(os.path.join(folder_path, "final_selected_folder"))


os.makedirs(os.path.join(folder_path, "final_selected_folder"), exist_ok=True)
folders = os.listdir(folder_path)
# final_selected_folder
sample_lists = []
for folder in folders:
    if generate_pages_range(os.path.join(folder_path, folder)) == 1:
        sample_lists.append(folder)
sample_lists = random.sample(sample_lists, int(number_of_files))
for folder in sample_lists:
    src = os.path.join(folder_path, folder)
    dst = os.path.join(folder_path, "final_selected_folder", folder)
    # copy the folder to the new location
    shutil.copytree(src, dst)
    print(f"Copied {folder} to final_selected_folder.")
print(f"Selected {len(sample_lists)} folders and moved them to 'final_selected_folder'.")
print("Process completed successfully.")