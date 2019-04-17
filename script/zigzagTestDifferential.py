#! /usr/bin/env python


import rospy
import atexit
from mavros_msgs.srv import CommandLong
from mavros_msgs.srv import CommandBool
from mavros_msgs.srv import SetMode
from std_msgs.msg import Float64
from mavros_msgs.msg import State

referenceCaptured=False
referenceDirection=-1000
compassDirection=0
mode = "MANUAL"
armed = False

# reference:
#	alternate (+500,-500) or (-500,+500). 
# our boat:
#	reverse:    1400
#	stop motor: 1500
#	foward:	    1600

#nothingPWM1 =1575
#nothingPWM2 =1100
#minPWM1 = 1220	# steering
#maxPWM1 = 1900
#minPWM2 = 900	# propulsor
#maxPWM2 = 1350
nothingPWM1 =0 # steering
nothingPWM2 =0 # propulsor
minPWM1 = -4500	# on lab try to use -450 
maxPWM1 = 4500   # on lab try to use 450 
minPWM2 = -100	# on lab try to use -50 
maxPWM2 = 100   # on lab try to use 20
PWM1 = minPWM1
PWM2 = minPWM2
state = 0
# states
# 0 waiting
# 1 going to +20 degrees
# 2 going to -20 degrees

rospy.init_node('zigzagTestNode')
rate = rospy.Rate(10)
rospy.wait_for_service('/mavros/cmd/command')
commandPWM = rospy.ServiceProxy('/mavros/cmd/command', CommandLong)
commandArming = rospy.ServiceProxy('/mavros/cmd/arming', CommandBool)
setMode = rospy.ServiceProxy('/mavros/set_mode', SetMode)

def exit_handler():
	global rate
	print 'Stop propeller'
	try:
		resp = commandPWM(0,183,0,4,nothingPWM1,0,0,0,0,0)
	except rospy.ServiceException, e:
		print "Service call failed: %s"%e
	rate.sleep()
	try:
		resp = commandPWM(0,183,0,2,nothingPWM2,0,0,0,0,0)
	except rospy.ServiceException, e:
		print "Service call failed: %s"%e
	rate.sleep()
	#print 'Trying to disarm!'
	#commandArming(False)


atexit.register(exit_handler)

def changeToState1():
	global state, commandPWM, rate
	state = 1
	try:
		resp = commandPWM(0,183,0,2,minPWM1,0,0,0,0,0)
		rate.sleep()
		resp = commandPWM(0,183,0,4,maxPWM2,0,0,0,0,0)
		rate.sleep()
	except rospy.ServiceException, e:
		print "Service call failed: %s"%e

def changeToState2():
	global state, commandPWM
	state = 2
	try:
		resp = commandPWM(0,183,0,2,maxPWM1,0,0,0,0,0)
		resp = commandPWM(0,183,0,4,minPWM2,0,0,0,0,0)
	except rospy.ServiceException, e:
		print "Service call failed: %s"%e

def arming():
	global commandArming, mode, armed
	if (armed==True):
		return True;
	resp = commandArming(True)
	rate.sleep()
	if (resp.success == True):
		return True
	print "Couldn't arm"
	return False

def setGuidedMode():
	global setMode
	resp = setMode(0,'guided')
	if (resp.mode_sent == True):
		return True
	print "Set guided mode failed"
	return False

def compassReader(data):
	global referenceCaptured, referenceDirection, compassDirection, state, commandPWM
#	rospy.loginfo("I read %f from compass",data.data)
#	if (referenceCaptured==False and setGuidedMode() and arming()):
	if (referenceCaptured==False and arming()):
		referenceDirection = data.data
		compassDirection = data.data
		referenceCaptured=True
		print "Reference angle: ",referenceDirection
		changeToState1()
	compassDirection=data.data

def stateReader(data):
	global mode, armed
	mode = data.mode
	armed = data.armed
	print(" armed: ", armed,"mode: ", mode);






def zigzagTest():
	global referenceCaptured, referenceDirection, compassDirection, state, commandPWM
	
#	rospy.spin()
	while not rospy.is_shutdown():
		if (referenceCaptured==False):
			continue;
		if (state == 0):
			continue;
		if (state == 1):
			print "State 1 angle: ", (compassDirection-referenceDirection)
			if ((compassDirection-referenceDirection) < -20):
				changeToState2()
		if (state == 2):
			print "state 2 angle: ", (compassDirection-referenceDirection)
			if ((compassDirection-referenceDirection) > 20):
				changeToState1()
		rate.sleep()


rospy.Subscriber('/mavros/global_position/compass_hdg',Float64,compassReader)
rospy.Subscriber('/mavros/state',State,stateReader)

if __name__== '__main__':
	try:
		zigzagTest()
	except rospy.ROSInterruptException:
		print "Closing application"
		pass




