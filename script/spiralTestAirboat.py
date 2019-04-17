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

#nothingPWM1 =1575 # steering
#nothingPWM2 =1100 # propulsor
#minPWM1 = 1220	# steering
#maxPWM1 = 1900
#minPWM2 = 900	# propulsor
#maxPWM2 = 1350
nothingPWM1 =0 # steering
nothingPWM2 =0 # propulsor
minPWM1 = -4500	# steering
maxPWM1 = 4500
minPWM2 = -50	# propulsor
maxPWM2 = 10
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
#pwm EXPECTED(1885, 1350,0),(1839,1350,12),(1764,1305,24),(1560,1350,42),(1355,1305,56),(1275,1314,72)
#PWM INSERTED(4292, 100,0 ),(3655,100,12), (2616,82,24),  (-190,100,42),(-2788, 82,56),(-3802,86,72)


speedArray =[
	#leftPWM, rightPWM, time(seconds)
	(4292,  maxPWM2,0 ),
	(3655,  maxPWM2,12),
	(2616,  maxPWM2*0.82,24), 
	(-190,  maxPWM2,42),
	(-2788, maxPWM2*0.82,56),
	(-3802, maxPWM2*0.86,72)
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
		resp = commandPWM(0,183,0,3,nothingPWM1,0,0,0,0,0)
	except rospy.ServiceException, e:
		print "Service call failed: %s"%e
	rate.sleep()
	try:
		resp = commandPWM(0,183,0,1,nothingPWM2,0,0,0,0,0)
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
		resp = commandPWM(0,183,0,1,speedArray[indexArray][0],0,0,0,0,0)
		rate.sleep()
		resp = commandPWM(0,183,0,3,speedArray[indexArray][1],0,0,0,0,0)
		rate.sleep()
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
	global setMode,mode
	if (mode=="GUIDED"):
		return True;
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




