#include <msp430.h>
static void clock_1mhz(void){
    CSCTL0_H = CSKEY_H;
    CSCTL1 = DCOFSEL_0;                              // 1 MHz DCO
    CSCTL2 = SELA__VLOCLK | SELS__DCOCLK | SELM__DCOCLK;
    CSCTL3 = DIVA__1 | DIVS__1 | DIVM__1;
    CSCTL0_H = 0;
}
static void uart1_init_9600(void){
    P3SEL1 &= ~(BIT4|BIT5); P3SEL0 |= (BIT4|BIT5);   // P3.4=TXD, P3.5=RXD (A1)
    UCA1CTLW0 = UCSWRST | UCSSEL__SMCLK;
    UCA1BRW   = 6;
    UCA1MCTLW = UCOS16 | (8<<4) | (0x20<<8);
    UCA1CTLW0 &= ~UCSWRST;
}
static void putc1(char c){ while(!(UCA1IFG & UCTXIFG)); UCA1TXBUF = c; }
static void puts1(const char*s){ while(*s) putc1(*s++); }
int main(void){
    WDTCTL = WDTPW | WDTHOLD;
    PM5CTL0 &= ~LOCKLPM5;                              // unlock GPIO
    clock_1mhz();
    uart1_init_9600();
    P1DIR |= BIT0;                                     // LED to prove we’re running
    for(;;){
        P1OUT ^= BIT0;
        puts1("Hello from FR6989!\r\n");
        __delay_cycles(1000000);
    }
}
