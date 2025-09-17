#include <msp430.h>
#define dly(c) __delay_cycles(c)

/* UART1 @9600 on P3.4/P3.5 */
static void uart1_init_9600(void){
    P3SEL1 &= ~(BIT4|BIT5); P3SEL0 |= (BIT4|BIT5);
    UCA1CTLW0 = UCSWRST | UCSSEL__SMCLK;
    UCA1BRW   = 6;
    UCA1MCTLW = UCOS16 | (8<<4) | (0x20<<8);
    UCA1CTLW0 &= ~UCSWRST;
}
static void putc1(char c){ while(!(UCA1IFG & UCTXIFG)); UCA1TXBUF = c; }
static void puts1(const char *s){ while(*s) putc1(*s++); }
static void putu8(unsigned char v){ char b[4]; int i=3; b[i]=0; do{ b[--i]='0'+(v%10); v/=10; }while(v); puts1(&b[i]); }

/* 1 MHz clock */
static void clock_1mhz(void){
    CSCTL0_H = CSKEY_H;
    CSCTL1 = DCOFSEL_0;
    CSCTL2 = SELA__VLOCLK | SELS__DCOCLK | SELM__DCOCLK;
    CSCTL3 = DIVA__1 | DIVS__1 | DIVM__1;
    CSCTL0_H = 0;
}

/* DHT11 on P1.7 */
#define DHT_BIT BIT7

/* One bit */
static unsigned char dht_read_bit(void){
    unsigned int t=0;
    while(!(P1IN & DHT_BIT));            // wait for HIGH
    while(P1IN & DHT_BIT){ __delay_cycles(1); t++; }
    return (t > 3) ? 1 : 0;              // cutoff ~3
}

/* Full frame */
static char dht_read(unsigned char *h, unsigned char *t){
    unsigned char data[5]={0,0,0,0,0};
    unsigned int i,j;

    // Start signal
    P1DIR |= DHT_BIT; P1OUT &= ~DHT_BIT; dly(18000);
    P1DIR &= ~DHT_BIT; dly(40);

    // Response
    unsigned int timeout=0;
    while(P1IN & DHT_BIT){ if(++timeout>1000) return 0; }
    timeout=0; while(!(P1IN & DHT_BIT)){ if(++timeout>1000) return 0; }
    timeout=0; while(P1IN & DHT_BIT){ if(++timeout>1000) return 0; }

    // 5 bytes = 40 bits
    for(i=0;i<5;i++){
        for(j=0;j<8;j++){
            data[i] <<= 1;
            data[i] |= dht_read_bit();
        }
    }

    if(((data[0]+data[1]+data[2]+data[3]) & 0xFF) != data[4]) return 0;

    *h = data[0];
    *t = data[2];
    return 1;
}

int main(void){
    WDTCTL = WDTPW | WDTHOLD;
    PM5CTL0 &= ~LOCKLPM5;
    clock_1mhz();
    uart1_init_9600();

    puts1("\r\nDHT11 minimal decode...\r\n");
    dly(2000000);

    unsigned char H,T;
    while(1){
        if(dht_read(&H,&T)){
            puts1("Humidity: "); putu8(H); puts1(" %  ");
            puts1("Temp: ");     putu8(T); puts1(" C\r\n");
        } else {
            puts1("DHT11 read failed\r\n");
        }
        dly(1000000);
    }
}
