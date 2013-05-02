#!/usr/bin/env python
#modified version of pose_classifier that can be used by mastermind.py
import roslib
roslib.load_manifest('rl_sentry')
import rospy
import tf
import fof
import sys
import numpy
sys.path.insert(0,'../libsvm-3.17/python')
from svmutil import *

from PyKDL import *

# array of joints to iterate over
JOINTS = ["head", "neck", "torso", "left_shoulder", "left_elbow", "right_shoulder", "right_elbow", "left_hip", "left_knee", "right_hip", "right_knee", "left_hand", "right_hand", "left_foot", "right_foot"]
joint_n = (11,4)

# array of states robot can be in
STATES = ["Neutral", "Friendly", "Hostile", "HOSTILE"]

#-------------------------------------------------------------
# Classify an individual frame as either friendly or hostile
# output confidence values 
#-------------------------------------------------------------
# params:
#   listener - used to find joint positions and orientations
#   m        - model used to classify frames
#-------------------------------------------------------------
# returns:
#   p_val    - confidence value of classification 
#-------------------------------------------------------------
def classify_frame(f,m):
  #f=frames
  #m is svm model

  #this can probably be moved else where
  frames = []
  joints = [[Rotation(1,0,0,0,1,0,0,0,1),Vector(0,0,0)]]*15
  data = numpy.array([float(v) for v in f.split(',')])

  index = 1
  for j in xrange(joint_n[0]):
    joints[j]=[Rotation(*data[index:index+9]),                # rotation matrix
               Vector(*data[index+10:index+13])]              # position
    index = index + 14
  for j in xrange(joint_n[0], joint_n[0]+joint_n[1]):
    joints[j]=[Rotation(1,0,0,0,1,0,0,0,1),Vector(*data[index:index+3])] # position
    index = index + 4
  
  frames.append(joints)  
  #endmove

  xp = []
  vect = fof.extractPoseFeature(frames)
  me=numpy.mean(vect)
  se=numpy.std(vect)
  vect[:]=[(p-float(me)/float(se)) for p in vect]
  xp.extend([vect])
  p_label, p_acc, p_val = svm_predict([0]*len(xp), xp, m, '-q')
  
  # PR2 Sentry States
  NEUTRAL  = 1
  FRIENDLY = 0
  WHOSTILE = 2  
  SHOSTILE = 3
  # Initial state is neutral  
  state = NEUTRAL  
  pval = [0]*10
  s_pval = 0
    
  
  print 'Current State: ', STATES[state], 'pval = ', s_pval

      
  # constantly shift in confidence values, use their sums to determine state transitions
  pval[:-1] = pval[1:]
  pval[-1] =  p_val[0][0]
  s_pval = sum(pval)
  if state == NEUTRAL:
    if s_pval > 9:
      state = FRIENDLY
      pval = [0]*10
    elif s_pval < -9:
      state = WHOSTILE
      pval = [0]*10
  elif state == FRIENDLY:
    if s_pval < -8:
      state = WHOSTILE
      pval = [0]*10
  elif state == WHOSTILE:     
    if s_pval > 9:
      state = NEUTRAL
      pval = [0]*10
    elif s_pval < -12:
      state = SHOSTILE
      pval = [0]*10
  else:
    if s_pval > 9:
      state = WHOSTILE 
      pval = [0]*10


  return state





