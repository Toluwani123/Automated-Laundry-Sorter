#include <msp430.h>
#include "dht11.h"
#define dly(c) __delay_cycles(c)

void dht11_init(void) {
    // DHT11 initialization
    P1DIR &= ~DHT_BIT;      // Set as input
    P1SEL0 &= ~DHT_BIT;     // GPIO function
    P1SEL1 &= ~DHT_BIT;
    P1REN |= DHT_BIT;       // Enable pull-up/pull-down resistor
    P1OUT |= DHT_BIT;       // Set as pull-up
}

/* One bit - SIMPLIFIED like working code */
static unsigned char dht_read_bit(void){
    /* Timeout-guarded edge waits so we never hang forever
       Keep thresholds compatible with your original logic */
    unsigned int width = 0;
    unsigned int guard = 0;

    // Wait for line to go HIGH (start of bit) with timeout
    while (!(P1IN & DHT_BIT)){
        if (++guard > 2000)        // ~2ms @ 1MHz with dly(1)
            return 0;              // treat as '0' on timeout
        dly(1);
    }

    // Measure HIGH width, bounded
    guard = 0;
    while (P1IN & DHT_BIT){
        dly(1);
        width++;
        if (++guard > 3000)        // cap so we don't loop forever
            break;
    }

    // Original cutoff (~3) preserved; adjust if needed after testing
    return (width > 3) ? 1 : 0;
}


/* Full frame - SIMPLIFIED like working code */
char dht11_read(unsigned char *h, unsigned char *t){
    unsigned char data[5]={0,0,0,0,0};
    unsigned int i,j;

    // Start signal - EXACTLY like working code
    P1DIR |= DHT_BIT;
    P1OUT &= ~DHT_BIT;
    dly(18000);                          // 18ms low
    P1DIR &= ~DHT_BIT;
    dly(40);                             // 40us wait

    // Response - with reasonable timeouts
    unsigned int timeout=0;
    while(P1IN & DHT_BIT){
        if(++timeout>1000) return 0;
        dly(1);
    }
    timeout=0;
    while(!(P1IN & DHT_BIT)){
        if(++timeout>1000) return 0;
        dly(1);
    }
    timeout=0;
    while(P1IN & DHT_BIT){
        if(++timeout>1000) return 0;
        dly(1);
    }

    // Read 40 bits - SIMPLE like working code
    for(i=0;i<5;i++){
        for(j=0;j<8;j++){
            data[i] <<= 1;
            data[i] |= dht_read_bit();
        }
    }

    // Checksum
    if(((data[0]+data[1]+data[2]+data[3]) & 0xFF) != data[4])
        return 0;

    *h = data[0];
    *t = data[2];
    return 1;
}
