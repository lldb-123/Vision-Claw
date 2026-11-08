#include "motion_protocol.h"
#include <string.h>
#include <stdio.h>
void MotionProtocol_Init(void){}
void MotionProtocol_OnLine(char *s){char c; long n; float v; if(sscanf(s,"MOVE %c %ld %f",&c,&n,&v)==3){Motion_MoveRelative(c=='Y'?MOTION_AXIS_Y:MOTION_AXIS_X,(int32_t)n,v);return;} if(sscanf(s,"GOTO %c %ld %f",&c,&n,&v)==3){Motion_Goto(c=='Y'?MOTION_AXIS_Y:MOTION_AXIS_X,(int32_t)n,v);return;} if(sscanf(s,"HOME %c",&c)==1){Motion_Home(c=='Y'?MOTION_AXIS_Y:MOTION_AXIS_X);return;} if(strncmp(s,"ESTOP",5)==0){Motion_EStop();return;} if(sscanf(s,"STOP %c",&c)==1){Motion_Stop(c=='Y'?MOTION_AXIS_Y:MOTION_AXIS_X);}}
