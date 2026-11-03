#include "host_protocol.h"
uint16_t Host_Crc16(const uint8_t *d,uint16_t n){uint16_t c=0xFFFF;for(uint16_t i=0;i<n;i++){c^=d[i];for(uint8_t j=0;j<8;j++)c=(c&1)?(c>>1)^0xA001:c>>1;}return c;}
