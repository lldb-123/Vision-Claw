#ifndef TRAY_CONTROL_H
#define TRAY_CONTROL_H

#include <stdint.h>
#include <stdbool.h>

typedef enum { TRAY_IDLE = 0, TRAY_RUNNING, TRAY_ESTOP } tray_state_t;
typedef enum { TRAY_DIR_NONE = 0, TRAY_DIR_CW, TRAY_DIR_CCW } tray_dir_t;

typedef struct {
    tray_state_t state;
    tray_dir_t direction;
    uint8_t speed;
    uint16_t pulse_us;
    uint32_t remaining_ms;
    bool open_loop;
} tray_status_t;

void Tray_Init(void);
bool Tray_Start(tray_dir_t direction, uint8_t speed, uint32_t duration_ms);
bool Tray_StartAngle(tray_dir_t direction, float angle_deg, uint8_t speed);
void Tray_Stop(void);
void Tray_EStop(void);
bool Tray_ClearFault(void);
void Tray_Service(void);
bool Tray_Snapshot(tray_status_t *out);

#endif
