#! /usr/bin/env python


import rospy
import atexit
from mavros_msgs.srv import CommandLong
from mavros_msgs.srv import CommandBool
from mavros_msgs.srv import SetMode
from std_msgs.msg import Float64


startingTime=-1
startedToRun=False

nothingPWM1 =1500
nothingPWM2 =1500
minPWM1 = 1100
maxPWM1 = 2000
minPWM2 = 1100
maxPWM2 = 2000
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
	(1600, 1440,0),
	(1600,1420,12),
	(1590,1510,24),
	(1550,1550,42),
	(1510,1590,56),
	(1420,1592,72)
]



rospy.init_node('zigzagTestNode')
rate = rospy.Rate(10)
rospy.wait_for_service('/mavros/cmd/command')
commandPWM = rospy.ServiceProxy('/mavros/cmd/command', CommandLong)
commandArming = rospy.ServiceProxy('/mavros/cmd/arming', CommandBool)
setMode = rospy.ServiceProxy('/mavros/set_mode', SetMode)


def exit_handler():
	print 'Trying to disarm!'
	commandArming(False)


atexit.register(exit_handler)

def incrementIndexArray():
	global indexArray, commandPWM, speedArray
	indexArray = indexArray+1
	try:
		print "indexArray: ",indexArray
		resp = commandPWM(0,183,0,1,speedArray[indexArray][0],0,0,0,0,0)
		rate.sleep()
		resp = commandPWM(0,183,0,3,speedArray[indexArray][1],0,0,0,0,0)
		rate.sleep()
	except rospy.ServiceException, e:
		print "Service call failed: %s"%e

def arming():
	global commandArming
	resp = commandArming(True)
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



def spiralTest():
	global  commandPWM, startingTime, startedToRun
	
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
		print "delta: ",delta," > ",speedArray[indexArray][2]
		if (delta > speedArray[indexArray][2]):
			incrementIndexArray()

		rate.sleep()



if __name__== '__main__':
	try:
		spiralTest()
	except rospy.ROSInterruptException:
		print "Closing application"
		pass




