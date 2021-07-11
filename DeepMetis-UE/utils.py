import json
import os
from os.path import exists, basename, splitext
import copy
import random
from glob import glob
from shutil import copyfile, rmtree


from properties import RESULTS_PATH, UNITY_STANDARD_IMGS_PATH
import chromosome_properties as chr_prop
import numpy as np


def get_distance(v1, v2):
    return np.linalg.norm(v1 - v2)


def print_archive(archive):
    path = RESULTS_PATH + '/archive'
    dst = path + '/'
    if not exists(dst):
        os.makedirs(dst)
    print(len(archive))

    for i, ind in enumerate(archive):

        seed = str(ind.seed)
        seed = seed.split('\\')
        seed = seed[-1][:-4]

        filename = dst + basename(
            'archived_' + str(i) +
            '_label_' + str(ind.member.eye_angle_1) +
            "_" + str(ind.member.eye_angle_2) +
            '_camera_' + str(ind.member.camera_angle_1) +
            "_" + str(ind.member.camera_angle_2) +
            '_seed_' + seed + ".jpg")

        #plt.imsave(filename, ind.member.representation, format='jpg')
        #imwrite(filename, ind.member.representation)
        with open(filename, 'wb') as f:
            f.write(ind.member.representation)

        filename2 = dst + basename(
            'archived_' + str(i) +
            '_label_' + str(ind.member.eye_angle_1) +
            "_" + str(ind.member.eye_angle_2) +
            '_camera_' + str(ind.member.camera_angle_1) +
            "_" + str(ind.member.camera_angle_2) +
            '_seed_' + seed)

        with open(splitext(filename2)[0]+'.json', 'w', encoding='utf-8') as f:
            json.dump(ind.member.model_params, f, ensure_ascii=False, indent=4)


        filename_base = dst + basename(
            'archived_' + str(i) + '_label_' + str(ind.member.eye_angle_1) + "_" + str(
                ind.member.eye_angle_2) + '_camera_' + str(ind.member.camera_angle_1) + "_" + str(
                ind.member.camera_angle_2) + '_seed_' + seed)
        np.save(filename_base, ind.member.img_np)



    solution_list = glob(dst + '/*.json')
    assert(len(solution_list) == len(archive))

# JSON UTILS
# DUPLICATE OF A METHOD FROM EYE INPUT - BAD
def get_json_data(json_file):
    with open(json_file) as data_file:
        data = json.load(data_file)
    return data

def fetch_label_from_json(data):
    e_a_1 = float(data['eye_angle_1'])
    e_a_2 = float(data['eye_angle_2'])

    e_a_1 = np.radians(e_a_1)
    e_a_2 = np.radians(e_a_2)

    eye_angles_rad = [e_a_1, e_a_2]

    return eye_angles_rad


def get_chromosome_property(element, type):
    param_name = element + "_" + type
    #example: element: pupil_size, type: low_bound/up_bound/mut_mgnt
    param_value = getattr(chr_prop, param_name)

    return param_value

def get_chromosome_property_triple(element):
    params = []

    param_name = element + "_" + "low_bound"
    params.append(getattr(chr_prop, param_name))

    param_name = element + "_" + "up_bound"
    params.append(getattr(chr_prop, param_name))

    param_name = element + "_" + "mut_mgnt"
    params.append(getattr(chr_prop, param_name))

    return params


def mutate_categorical_parameter(param_name, old_value):
    values = copy.copy(getattr(chr_prop, param_name))

    if old_value in values:
        values.remove(old_value)

    new_value = random.choice(values)

    return new_value


def mutate_continuous_parameter(param_name, old_value):
    param_values = get_chromosome_property_triple(param_name)

    condition = True
    while(condition):
        displacement = random.uniform((-1) * param_values[2], param_values[2])

        new_value = old_value + displacement
        new_value = np.clip(new_value, a_min=param_values[0], a_max=param_values[1])

        if abs(new_value - old_value) > param_values[2]/10:
            condition = False

    return new_value


def mutate_integer_parameter(param_name, old_value):
    param_values = get_chromosome_property_triple(param_name)

    condition = True
    while(condition):
        displacement = random.randint((-1) * param_values[2], param_values[2])

        new_value = old_value + displacement
        new_value = np.clip(new_value, a_min=param_values[0], a_max=param_values[1])
        if new_value != old_value:
            condition = False

    return new_value

def mutate_circular_parameter(param_name, old_value):
    param_values = get_chromosome_property_triple(param_name)

    condition = True
    while(condition):
        displacement = random.randint((-1) * param_values[2], param_values[2])

        new_value = old_value + displacement
        new_value = new_value % 360
        # new_value = np.clip(new_value, a_min=param_values[0], a_max=param_values[1])
        if new_value != old_value:
            condition = False

    return new_value

def update_jsons_with_angles(folder, camera_angle_1, camera_angle_2, eye_angle_1, eye_angle_2):
    json_files = glob(folder + "\*.json")


    for json_file in json_files:
        data = get_json_data(json_file)

        data['camera_angle_1'] = str(camera_angle_1)
        data['camera_angle_2'] = str(camera_angle_2)
        data['eye_angle_1'] = str(eye_angle_1)
        data['eye_angle_2'] = str(eye_angle_2)

        with open(json_file, "w") as write_file:
            json.dump(data, write_file, indent=4)


def handleRemoveReadonly(func, path, exc):
    import errno, os, stat, shutil
    excvalue = exc[1]
    if func in (os.rmdir, os.remove) and excvalue.errno == errno.EACCES:
      os.chmod(path, stat.S_IRWXU| stat.S_IRWXG| stat.S_IRWXO) # 0777
      func(path)
    else:
      raise

def rename_generated_imgs_folder(imgs_folder, camera_angle_1, camera_angle_2, eye_angle_1, eye_angle_2):
    if exists(imgs_folder):
        json_s = ".json"
        jpg_s = ".jpg"

        json_files = glob(UNITY_STANDARD_IMGS_PATH + "\*.json")
        base_files = glob(imgs_folder + "\*.json")
        base_num = len(base_files)
        assert (base_num > 0)

        update_jsons_with_angles(UNITY_STANDARD_IMGS_PATH, camera_angle_1, camera_angle_2, eye_angle_1, eye_angle_2)

        for json_file in json_files:
            file_name = os.path.abspath(json_file).replace(os.path.abspath(UNITY_STANDARD_IMGS_PATH), '')
            file_num = int(file_name[1:-5])
            new_file_num = file_num + base_num

            new_file_name_json = os.path.join(imgs_folder, (str(new_file_num) + json_s))
            assert(os.path.isfile(new_file_name_json) == False)

            old_name_jpg = json_file.replace(json_s, jpg_s)
            new_file_name_jpg = os.path.join(imgs_folder, (str(new_file_num) + jpg_s))

            copyfile(json_file, new_file_name_json)
            copyfile(old_name_jpg, new_file_name_jpg)

        rmtree(UNITY_STANDARD_IMGS_PATH)
    else:
        # print("Rename generated img folder: folder does NOT already exists")
        #time.sleep(.0000000000000001)
        #os.rename(UNITY_STANDARD_IMGS_PATH, imgs_folder)
        renamedir_loop(UNITY_STANDARD_IMGS_PATH, imgs_folder)
        update_jsons_with_angles(imgs_folder, camera_angle_1, camera_angle_2, eye_angle_1, eye_angle_2)

    # Create new 'imgs' folder for future generations
    if not exists(UNITY_STANDARD_IMGS_PATH):
        #time.sleep(.0000000000000001)
        #os.mkdir(UNITY_STANDARD_IMGS_PATH)
        makedir_loop(UNITY_STANDARD_IMGS_PATH)

def makedir_loop(dir):
    try:
        os.mkdir(dir)
    except:
        makedir_loop(dir)

def renamedir_loop(old_name, new_name):
    try:
        os.rename(old_name, new_name)
    except:
        renamedir_loop(old_name, new_name)

