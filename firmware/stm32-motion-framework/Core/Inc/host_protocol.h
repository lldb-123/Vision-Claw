#ifndef HOST_PROTOCOL_H
#define HOST_PROTOCOL_H
#include <stdint.h>
#define HOST_SOF1 0x55
#define HOST_SOF2 0xAA
#define HOST_CMD_MOVE 0x01
#define HOST_CMD_GOTO 0x02
#define HOST_CMD_HOME 0x03
#define HOST_CMD_SERVO 0x04
#define HOST_CMD_STOP 0x05
#define HOST_EVT_STATUS 0x81
#define HOST_EVT_SENSOR 0x82
uint16_t Host_Crc16(const uint8_t *data,uint16_t len);
#endif
