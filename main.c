#include <msp430.h>
#define dly(cyc) __delay_cycles(cyc)

/* ---------------- UART1: 9600 8N1 on P3.4/P3.5 ---------------- */
static void uart1_init_9600(void){
    // Route P3.4=UCA1TXD, P3.5=UCA1RXD
    P3SEL1 &= ~(BIT4|BIT5);
    P3SEL0 |=  (BIT4|BIT5);

    UCA1CTLW0 = UCSWRST | UCSSEL__SMCLK;         // hold eUSCI; SMCLK source
    // 1 MHz -> 9600, oversampling
    UCA1BRW   = 6;
    UCA1MCTLW = UCOS16 | (8 << 4) | (0x20 << 8); // UCBRF=8, UCBRS≈0x20
    UCA1CTLW0 &= ~UCSWRST;                       // enable UART
}
static void putc1(char c){ while(!(UCA1IFG & UCTXIFG)); UCA1TXBUF = c; }
static void puts1(const char*s){ while(*s) putc1(*s++); }
static void putu32(unsigned long v){
    char b[11]; int i=10; b[i]=0;
    do{ b[--i] = '0' + (v%10); v/=10; }while(v);
    puts1(&b[i]);
}

/* ---------------- 1 MHz clocks & TimerA0 free-running ---------------- */
static void clock_1mhz(void){
    CSCTL0_H = CSKEY_H;
    CSCTL1 = DCOFSEL_0;                                   // 1 MHz DCO
    CSCTL2 = SELA__VLOCLK | SELS__DCOCLK | SELM__DCOCLK;  // ACLK=VLO, SMCLK/MCLK=DCO
    CSCTL3 = DIVA__1 | DIVS__1 | DIVM__1;
    CSCTL0_H = 0;
}
static void timer0_init(void){
    TA0CTL = TASSEL__SMCLK | MC__CONTINUOUS | TACLR;      // 1 MHz free-run
}

/* ---------------- TCS3200 wiring (your pins) ----------------
   OUT -> P1.6 (interrupt input)
   S0  -> P2.6   S1 -> P2.7
   S2  -> P2.3   S3 -> P2.4
   VCC 3.3V, GND common. No OE pin on your module.
---------------------------------------------------------------- */
#define TCS_S0 BIT6   // P2.6
#define TCS_S1 BIT7   // P2.7
#define TCS_S2 BIT3   // P2.3
#define TCS_S3 BIT4   // P2.4

static void tcs_pins_init(void){

    P2DIR |= (TCS_S0|TCS_S1|TCS_S2|TCS_S3);


    P2OUT |= (TCS_S0 | TCS_S1);

    // OUT on P1.6 as GPIO input
    P1DIR  &= ~BIT6;
    P1SEL0 &= ~BIT6; P1SEL1 &= ~BIT6;
    P1IES  &= ~BIT6;                    // rising edge
    P1IFG  &= ~BIT6;                    // clear flags
    P1IE   |=  BIT6;                    // enable interrupt
}

/* ---------------- Period Calculation for ISR---------------- */
static volatile unsigned int  g_last = 0;
static volatile unsigned int  g_period = 0;
static volatile unsigned int  g_edges = 0;

#pragma vector=PORT1_VECTOR
__interrupt void PORT1_ISR(void){
    if (P1IFG & BIT6){
        unsigned int now = TA0R;
        unsigned int dt  = now - g_last;
        g_last = now;
        if (dt){ g_period = dt; g_edges++; }
        P1IFG &= ~BIT6;
    }
}

/* ---------------- Filter helpers ---------------- */
static inline void tcs_filter_red(void)   { P2OUT &= ~(TCS_S2|TCS_S3); }          // S2=0,S3=0
static inline void tcs_filter_green(void) { P2OUT |=  (TCS_S2|TCS_S3); }          // 1,1
static inline void tcs_filter_blue(void)  { P2OUT &= ~TCS_S2; P2OUT |= TCS_S3; }  // 0,1


/* Average periods with a simple timeout based on sample size provided. Returns 0 if no edges. */
static unsigned long measure_avg_period(unsigned int samples, unsigned int timeout_us){
    unsigned int last = g_edges;
    unsigned long sum = 0;
    unsigned int  got = 0;
    unsigned int  t0  = TA0R;
    while (got < samples){
        if (g_edges != last){
            last = g_edges;
            sum += g_period;
            got++;
            t0 = TA0R;     // reset timeout after each edge
        }
        if ((unsigned int)(TA0R - t0) > timeout_us) break;
    }
    return got ? (sum / got) : 0;
}

int main(void){
    WDTCTL = WDTPW | WDTHOLD;
    PM5CTL0 &= ~LOCKLPM5;            // unlock GPIO

    clock_1mhz();                    // Clock Call
    uart1_init_9600();               // UART Setup Call
    timer0_init();                   // Timer 0 Setup call
    tcs_pins_init();                 // Pin COnfig
    __enable_interrupt();            // Enable ISR's

    puts1("\r\nTCS3200 quick test running...\r\n");

    for(;;){
        unsigned long pr=0, pg=0, pb=0; // Periods for color
        unsigned long fr=0, fg=0, fb=0; // Frequencies for colors



        // ---- Measure Red ----
        tcs_filter_red();
        dly(20000);
        pr = measure_avg_period(40, 120000);
        if (pr) fr = 1000000UL / pr;

        // ---- Measure Green ----
        tcs_filter_green();
        dly(20000);
        pg = measure_avg_period(40, 120000);
        if (pg) fg = 1000000UL / pg;

        // ---- Measure Blue ----
        tcs_filter_blue();
        dly(20000);
        pb = measure_avg_period(40, 120000);
        if (pb) fb = 1000000UL / pb;

        unsigned long brightness_sum = fr + fg + fb;
        float r_ratio = (float)fr / brightness_sum;
        float g_ratio = (float)fg / brightness_sum;
        float b_ratio = (float)fb / brightness_sum;
        unsigned long brightness_avg = brightness_sum / 3;

        if (fr|fg|fb){
            puts1("R="); putu32(fr);
            puts1(" Hz, G="); putu32(fg);
            puts1(" Hz, B="); putu32(fb);
            puts1(" Hz  ");

            // 1. Dominant color detection
            if (r_ratio > 0.45 && g_ratio < r_ratio && b_ratio < r_ratio) {
                puts1("=> RED ");
            } else if (g_ratio > 0.36 && g_ratio > r_ratio && g_ratio > b_ratio) {
                puts1("=> GREEN ");
            } else if (b_ratio > 0.40 && r_ratio < 0.35 && g_ratio < 0.35) {
                puts1("=> BLUE ");

            } else {
                puts1("=> MIXED/OTHER ");
            }

            // 2. Light vs Dark classification


            if (brightness_avg > 7000) {
                puts1("=> LIGHT CLOTHES\r\n");
            } else {
                puts1("=> DARK CLOTHES\r\n");
            }

        } else {
            puts1("no signal (check OUT=P1.6, power, light)\r\n");
        }

        dly(500000); //0.5s delay
    }

}
