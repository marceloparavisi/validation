#! /usr/bin/env python


import rospy
import atexit
from mavros_msgs.srv import CommandLong
from mavros_msgs.srv import CommandBool
from mavros_msgs.srv import SetMode
from std_msgs.msg import Float64
from mavros_msgs.msg import State

startingTime=-1
startedToRun=False
mode = "MANUAL"
armed = False

nothingPWM1 =0.0
nothingPWM2 =0.0
minPWM1 = -4500.0
maxPWM1 = 450.0
minPWM2 = -100.0
maxPWM2 = 100.0
PWM1 = minPWM1
PWM2 = minPWM2
indexArray = 0
# arrayIndex
# -1 waiting
# 0 executing PWM speeds of index array zero
# 1 executing PWM speeds of index array one

# our boat:
#	reverse:    1400
#	stop motor: 1500
#	foward:	    1600
# reference plan:
#	(1000,-400,0);(1000,-200,12); (900,100,24); (500 ,500 ,42); (100,900,56);(-200,920,72)
# our plan:
#	(1600, 1440,0),(1600,1420,12),(1590,1510,24),(1550,1550,42),(1510,1590,56),(1420,1592,72)


speedArray =[
	#leftPWM, rightPWM, time(seconds)
	(1.0*maxPWM1,	0.400*minPWM2-0.5,0),
	(1.0*maxPWM1,	0.200*minPWM2-0.5,12),
	(0.9*maxPWM1,	0.100*maxPWM2+0.1,24), 
	(0.5*maxPWM1,	0.500*maxPWM2,42), 
	(0.1*maxPWM1+0.1,	0.900*maxPWM2,56),
	(0.200*minPWM1-0.5,	0.920*maxPWM2,72)
]

speedArray =[
	#leftPWM, rightPWM, time(seconds)
	(1.0*maxPWM1,	(0.5+0.4)*minPWM2,0),
	(1.0*maxPWM1,	(0.5+0.2)*minPWM2,2),
	(0.9*maxPWM1,	(0.1+0.1)*maxPWM2,4), 
	(0.5*maxPWM1,	0.5*maxPWM2,6), 
	((0.1)*maxPWM1,	0.9*maxPWM2,8),
	((0.2)*minPWM1,	0.92*maxPWM2,10)
]



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

def incrementIndexArray():
	global indexArray, commandPWM, speedArray
	indexArray = indexArray+1
	if (indexArray >= len(speedArray)):
		exit();
	try:
		print "indexArray: ",indexArray
		resp = commandPWM(0,183,0,2,speedArray[indexArray][0],0,0,0,0,0)
		rate.sleep()
		resp = commandPWM(0,183,0,4,speedArray[indexArray][1],0,0,0,0,0)
		rate.sleep()
	except rospy.ServiceException, e:
		print "Service call failed: %s"%e

def arming():
	global commandArming, mode, armed
	if (armed==True):
		return True;
	resp = commandArming(True)
	if (resp.success == True):
		return True
	print "Couldn't arm"
	return False

def setGuidedMode():
	global setMode, mode
	if (mode=="GUIDED"):
		return True;
	resp = setMode(0,'guided')
	if (resp.mode_sent == True):
		return True
	print ("Set guided mode failed. Mode: ",mode)
	return False



def spiralTest():
	global  commandPWM, startingTime, startedToRun, indexArray
	
#	rospy.spin()
	while not rospy.is_shutdown():
		
		if (startedToRun==False):
			if(setGuidedMode() and arming()):
				now = rospy.get_rostime()
				startingTime = now.secs+now.nsecs/1000000000.0
				startedToRun = True
			else:
				continue;
		now = rospy.get_rostime()
		delta = now.secs + now.nsecs/1000000000 - startingTime
		print "delta: ",delta," > ",speedArray[indexArray][2], " pwm: ",speedArray[indexArray][0],speedArray[indexArray][1]
		if (delta > speedArray[indexArray][2]):
			incrementIndexArray()

		rate.sleep()

def stateReader(data):
	global mode, armed
	mode = data.mode
	armed = data.armed
	print(" armed: ", armed,"mode: ", mode);

rospy.Subscriber('/mavros/state',State,stateReader)


if __name__== '__main__':
	try:
		spiralTest()
	except rospy.ROSInterruptException:
		print "Closing application"
		pass




