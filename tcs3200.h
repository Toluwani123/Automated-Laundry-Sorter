#ifndef TCS3200_H
#define TCS3200_H

// Pin definitions - use unique names
#define TCS_S0_PIN BIT6   // P2.6
#define TCS_S1_PIN BIT7   // P2.7
#define TCS_S2_PIN BIT3   // P2.3
#define TCS_S3_PIN BIT4   // P2.4
#define TCS_OUT_PIN BIT4  // P1.4

void tcs3200_init(void);
void tcs3200_measure(unsigned long *red, unsigned long *green, unsigned long *blue);

#endif
