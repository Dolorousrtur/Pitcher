import json
from enum import Enum
import numpy as np
from numpy.linalg import norm
import sched, time
import os

class Position(Enum):
    NORMAL = 1
    ROTATED = 2
    CLOSED = 3
    POCKETS = 4
    TOUCHING = 5


class BodyPart(Enum):
    FACE = 0
    NECK = 1
    LEFT_SHOULDER = 2
    LEFT_ELBOW = 3
    LEFT_WRIST = 4
    RIGHT_SHOULDER = 5
    RIGHT_ELBOW = 6
    RIGHT_WRIST = 7
    LEFT_HIP = 8
    LEFT_KNEE = 9
    LEFT_ANKLE = 10
    RIGHT_HIP = 11
    RIGHT_KNEE = 12
    RIGHT_ANKLE = 13
    LEFT_EYE = 14
    RIGHT_EYE = 15
    LEFT_EAR = 16
    RIGHT_EAR = 17

class JsonReader:
    def __init__(self, file_dir, callback):
        self.file_dir = file_dir
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.callback = callback
        
    def getOutput(self, fileName):
        pts = getKeypointsFromJsonFile(fileName)

        pts = convertKeypointsToBodyParts(pts)
        self.callback(classifyPosition(pts))

    def startProcessing(self):
        i = 0
        for parentPath, _, fileNames in os.walk(self.file_dir):
            for fileName in sorted(fileNames):
                fullname = os.path.join(parentPath, fileName)
                i+=1
                self.scheduler.enter(1./30*i, 1, self.getOutput, argument=(fullname, ))

        self.scheduler.run()

def getKeypointsFromJsonFile(jsonFilePath):
    with open(jsonFilePath, 'r') as jsonFile:
        jso =  json.load(jsonFile)
    
    if jso is None:
        raise Exception('can\'t read file')

    people = jso['people']
    if len(people) > 1:
        raise Exception('there\'s more than one person on the photo')

    people = people[0]
    keypoints = people['pose_keypoints']
    return keypoints

def convertKeypointsToBodyParts(keypoints):
    groupedKeypoints = []
    for i in range(int(len(keypoints)/3)):
        groupedKeypoints.append((keypoints[3*i], keypoints[3*i + 1], keypoints[3*i + 2]))
    return groupedKeypoints

def classifyPosition(keypoints):

    left_shoulder = np.array(keypoints[BodyPart.LEFT_SHOULDER.value][:2])

    right_shoulder = np.array(keypoints[BodyPart.RIGHT_SHOULDER.value][:2])
    
    left_elbow = np.array(keypoints[BodyPart.LEFT_ELBOW.value][:2])
    right_elbow = np.array(keypoints[BodyPart.RIGHT_ELBOW.value][:2])

    left_wrist = np.array(keypoints[BodyPart.LEFT_WRIST.value][:2])
    right_wrist = np.array(keypoints[BodyPart.RIGHT_WRIST.value][:2])

    neck = np.array(keypoints[BodyPart.NECK.value][:2])
    face = np.array(keypoints[BodyPart.FACE.value][:2])

    right_hip = np.array(keypoints[BodyPart.RIGHT_HIP.value][:2])
    left_hip = np.array(keypoints[BodyPart.LEFT_HIP.value][:2])

    right_knee = np.array(keypoints[BodyPart.RIGHT_KNEE.value][:2])
    left_knee = np.array(keypoints[BodyPart.LEFT_KNEE.value][:2])

    right_ankle = np.array(keypoints[BodyPart.RIGHT_ANKLE.value][:2])
    left_ankle = np.array(keypoints[BodyPart.LEFT_ANKLE.value][:2])
    
    #back to the audience
    shldiff = np.abs(left_shoulder - right_shoulder)
    angle_to_horizon = np.arctan(shldiff[1] / shldiff[0])
    if angle_to_horizon > np.pi/6:
        return Position.ROTATED

    #crossed arms/closed position
    distance_between_shoulders = np.linalg.norm(left_shoulder - right_shoulder)

    distanceThreshold = distance_between_shoulders / 4
 
    if norm(left_wrist - right_shoulder) < distanceThreshold or norm(left_wrist - right_elbow) < distanceThreshold  or norm(left_wrist - right_hip) < distanceThreshold or norm(right_wrist - left_shoulder) < distanceThreshold or norm(right_wrist - left_elbow) < distanceThreshold  or norm(right_wrist - left_hip) < distanceThreshold:
        return Position.CLOSED

    #arms in the pockets
    pocketTresh = distance_between_shoulders / 8
    if norm(left_wrist - left_hip) < pocketTresh or norm(right_wrist - right_hip) < pocketTresh:
        return Position.POCKETS

    #crossed legs
    if norm(right_ankle[0] - left_ankle[0]) < 0:
        return Position.CLOSED

    #touching neck
    if norm(left_wrist - neck) < pocketTresh or norm(right_wrist - neck) < pocketTresh or norm(left_wrist - face) < pocketTresh or norm(right_wrist - face) < pocketTresh:
        return Position.TOUCHING

    return Position.NORMAL

