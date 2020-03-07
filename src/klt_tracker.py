import cv2
import matplotlib.pyplot as plt
import numpy as np
from utilities import *
from itertools import compress

class KLT_Tracker:
    
    def __init__(self, images, feature_params, lk_params):
        self.reference_image = images[0]
        self.images = images[1:]
        self.feature_params = feature_params
        self.lk_params = lk_params
        self.reference_features = self.get_features()
        self.optical_flow = [ [(i.ravel()[0], i.ravel()[1])] for i in self.reference_features]

    def get_features(self):
        return cv2.goodFeaturesToTrack(gray(self.reference_image), 
                                mask = None, 
                                **self.feature_params)

    def generate_optical_flow(self):


        optical_flow = self.optical_flow
        reference_features = self.reference_features
        for current_image in self.images:
            current_features, status, error = cv2.calcOpticalFlowPyrLK(gray(self.reference_image), 
                                                                       gray(current_image), 
                                                                       reference_features, 
                                                                       None, 
                                                                       **self.lk_params)

            reference_features = reference_features[status == 1]
            current_features = current_features[status == 1]

            optical_flow = [optical_flow[i] for i, j in enumerate(status) if j == 1]

            for i, feature in enumerate(current_features):
                optical_flow[i].append((feature.ravel()[0], feature.ravel()[1]))

            reference_features = reference_features.reshape((reference_features.shape[0],1,2))

        self.reference_features = reference_features
        self.optical_flow = optical_flow

        return optical_flow
        
    def draw_optical_flow(self):
        image = self.reference_image.copy()
        mask = np.zeros_like(image)
        for feature in self.optical_flow:
            feature = np.array(feature, np.int32).reshape((-1,1,2))
            cv2.polylines(mask, [feature], False, (255,0,0))
        image = cv2.add(image, mask)
        plt.imshow(image)
        plt.show()
    
    def homography_filter(self, threshold = 0.9):
        '''
        Function to remove outliers points from optical flow
        '''
        
        no_of_cams = len(self.optical_flow[0])
        no_of_pts = len(self.optical_flow)

        image_pts = np.zeros((no_of_cams, no_of_pts, 2))

        # creating image_pts with dimensions as camId, pointId, 2
        for i in range(no_of_pts):
            for j in range(no_of_cams):

                image_pts[j, i, 0] = self.optical_flow[i][j][0]
                image_pts[j, i, 1] = self.optical_flow[i][j][1]

        reference_image_pts = image_pts[0, :, :]    

        mask = np.zeros((no_of_pts, 1))
        
        # calculating the number of frames each point is an inlier in
        for j in range(1, no_of_cams):
            
            homography_matrix, inliers = cv2.findHomography(image_pts[j, :, :], reference_image_pts, cv2.RANSAC, 3.0)
            mask = mask + inliers
        
        # mask ensuring points present in cameras below the threshold percentage are removed 

        mask = (mask >= threshold * no_of_cams)

        self.optical_flow = list(compress(self.optical_flow, mask))

        return self.optical_flow



    def generate_initial_point_cloud(self, point_cloud_path):
        reference_features = self.reference_features.reshape(self.reference_features.shape[0], 2).astype('uint8')
        reference_features_textures = self.reference_image[reference_features[:,0], reference_features[:,1], :]
        # reference_features_points = np.concatenate((reference_features, np.zeros((reference_features.shape[0], 1))), axis =1)
        reference_features_points = np.concatenate((reference_features, np.random.uniform(2, 4, (reference_features.shape[0], 1))), axis =1)
        # Scale the points correctly
        write_point_cloud(point_cloud_path, reference_features_points, reference_features_textures)

    def generate_bundle_file(self, bundle_file_path):
        pass
    




