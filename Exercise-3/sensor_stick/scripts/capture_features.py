#!/usr/bin/env python
import numpy as np
import pickle
import rospy
import argparse

from sensor_stick.pcl_helper import *
from sensor_stick.training_helper import spawn_model
from sensor_stick.training_helper import delete_model
from sensor_stick.training_helper import initial_setup
from sensor_stick.training_helper import capture_sample
from sensor_stick.features import compute_color_histograms
from sensor_stick.features import compute_normal_histograms
from sensor_stick.srv import GetNormals
from geometry_msgs.msg import Pose
from sensor_msgs.msg import PointCloud2


def get_normals(cloud):
    get_normals_prox = rospy.ServiceProxy('/feature_extractor/get_normals', GetNormals)
    return get_normals_prox(cloud).cluster


if __name__ == '__main__':
    rospy.init_node('capture_node')

    # Argument Parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--list', action='store', dest='num',
                    help='Pick a valid list number', type=int, required=True)
    parser.add_argument('-t', '--times', action='store', dest='num_times', default = 50,
                    help='Number of times to capture features for each model', type=int)
    parser.add_argument('-no_hsv', action='store_false', dest='flag', default = True,
                    help='Compute color hist using HSV')
    args = parser.parse_args()
    pick_list = args.num
    ntimes = args.num_times
    hsv_flag = args.flag

    # Capture features based on user input
    if pick_list == 1:
        print("Capturing features for pick_list_1")
        models = [\
           'biscuits',
           'soap',
           'soap2']
    elif pick_list == 2:
        print("Capturing features for pick_list_2")
        models = [\
           'biscuits',
           'soap',
           'book',
           'soap2',
           'glue']
    elif pick_list == 3:
        print("Capturing features for pick_list_3")
        models = [\
           'sticky_notes',
           'book',
           'snacks',
           'biscuits',
           'eraser',
           'soap2',
           'soap',
           'glue']
    else:
        print("Capturing features for general list")
        models = [\
           'beer',
           'bowl',
           'create',
           'disk_part',
           'hammer',
           'plastic_cup',
           'soda_can']


    # Disable gravity and delete the ground plane
    initial_setup()
    labeled_features = []

    for model_name in models:
        spawn_model(model_name)

        for i in range(ntimes):
            # make five attempts to get a valid a point cloud then give up
            sample_was_good = False
            try_count = 0
            while not sample_was_good and try_count < 5:
                sample_cloud = capture_sample()
                sample_cloud_arr = ros_to_pcl(sample_cloud).to_array()

                # Check for invalid clouds.
                if sample_cloud_arr.shape[0] == 0:
                    print('Invalid cloud detected')
                    try_count += 1
                else:
                    sample_was_good = True

            # Extract histogram features
            chists = compute_color_histograms(sample_cloud, using_hsv=hsv_flag)
            normals = get_normals(sample_cloud)
            nhists = compute_normal_histograms(normals)
            feature = np.concatenate((chists, nhists))
            labeled_features.append([feature, model_name])

        delete_model()

    file_name = 'training_set_' + str(pick_list) + '.sav'
    pickle.dump(labeled_features, open(file_name, 'wb'))

