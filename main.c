#include <msp430.h>
#include "dht11.h"
#include "tcs3200.h"
#include <stdint.h>

#define dly(cyc) __delay_cycles(cyc)

// System States
typedef enum {
    STATE_IDLE,
    STATE_READ_HUMIDITY,
    STATE_READ_COLOR,
    STATE_DECIDE_BASKET,
    STATE_ACTUATE,
    STATE_ERROR
} system_state_t;

// Basket types
typedef enum {
    BASKET_DRY_LIGHT,
    BASKET_DRY_DARK,
    BASKET_DAMP_LIGHT,
    BASKET_DAMP_DARK,
    BASKET_UNKNOWN
} basket_t;

// Global variables
static system_state_t current_state = STATE_IDLE;
static unsigned char humidity = 0;
static unsigned char temperature = 0;
static unsigned long red_freq = 0, green_freq = 0, blue_freq = 0;
static basket_t target_basket = BASKET_UNKNOWN;

// Thresholds - adjust based on your testing
#define HUMIDITY_THRESHOLD 70    // % above which clothing is considered damp
#define BRIGHTNESS_THRESHOLD 5200 // Your existing threshold

/* UART Functions */
static void uart1_init_9600(void){
    P3SEL1 &= ~(BIT4|BIT5);
    P3SEL0 |= (BIT4|BIT5);
    UCA1CTLW0 = UCSWRST | UCSSEL__SMCLK;
    UCA1BRW   = 6;
    UCA1MCTLW = UCOS16 | (8<<4) | (0x20<<8);
    UCA1CTLW0 &= ~UCSWRST;
}

static void putc1(char c){
    while(!(UCA1IFG & UCTXIFG));
    UCA1TXBUF = c;
}

static void puts1(const char *s){
    while(*s) putc1(*s++);
}

static void putu8(unsigned char v){
    char b[4];
    int i=3;
    b[i]=0;
    do{
        b[--i]='0'+(v%10);
        v/=10;
    } while(v);
    puts1(&b[i]);
}

static void putu32(unsigned long v){
    char b[11];
    int i=10;
    b[i]=0;
    do{
        b[--i] = '0' + (v%10);
        v/=10;
    } while(v);
    puts1(&b[i]);
}

/* 1 MHz clock */
static void clock_1mhz(void){
    CSCTL0_H = CSKEY_H;
    CSCTL1 = DCOFSEL_0;
    CSCTL2 = SELA__VLOCLK | SELS__DCOCLK | SELM__DCOCLK;
    CSCTL3 = DIVA__1 | DIVS__1 | DIVM__1;
    CSCTL0_H = 0;
}

/* Timer for TCS3200 */
void timer0_init(void){
    TA0CTL = TASSEL__SMCLK | MC__CONTINUOUS | TACLR;
}

/* Classification Logic */
basket_t classify_clothing(unsigned char hum, unsigned long r, unsigned long g, unsigned long b) {
    if (r == 0 && g == 0 && b == 0) {
        return BASKET_UNKNOWN; // No color data
    }

    unsigned long brightness_sum = r + g + b;
    if (brightness_sum == 0) return BASKET_UNKNOWN;

    float r_ratio = (float)r / brightness_sum;
    float g_ratio = (float)g / brightness_sum;
    float b_ratio = (float)b / brightness_sum;
    unsigned long brightness_avg = brightness_sum / 3;

    // Determine if dark or light (using your existing threshold)
    int is_dark = (brightness_avg <= BRIGHTNESS_THRESHOLD);
    int is_damp = (hum >= HUMIDITY_THRESHOLD);

    // Classification logic
    if (is_damp) {
        return is_dark ? BASKET_DAMP_DARK : BASKET_DAMP_LIGHT;
    } else {
        return is_dark ? BASKET_DRY_DARK : BASKET_DRY_LIGHT;
    }
}

/* State Machine */
void run_state_machine(void) {
    switch(current_state) {
        case STATE_IDLE:
            puts1("\r\n=== Starting Measurement ===\r\n");
            current_state = STATE_READ_HUMIDITY;
            break;

        case STATE_READ_HUMIDITY:
            puts1("Reading humidity... ");

            // Remove this debug section - it interferes with timing
            // if(P1IN & DHT_BIT) {
            //     puts1("(Line HIGH) ");
            // } else {
            //     puts1("(Line LOW) ");
            // }

            // Reset DHT11 pin
            P1DIR &= ~DHT_BIT;
            P1REN |= DHT_BIT;
            P1OUT |= DHT_BIT;
            dly(100000); // 100ms stabilization

            /* --- pause TCS3200 interrupt during DHT transaction --- */
            uint8_t saved_p1ie = P1IE;          // save Port 1 interrupt enable state
            P1IE &= ~TCS_OUT_PIN;               // mask TCS3200 OUT interrupt (from tcs3200.h)
            __disable_interrupt();              // avoid preemption during tight DHT timing

            char ok = dht11_read(&humidity, &temperature);

            __enable_interrupt();
            P1IFG &= ~TCS_OUT_PIN;              // clear any pending edge captured while masked
            P1IE = saved_p1ie;                  // restore Port 1 interrupt enables
            /* ------------------------------------------------------ */

            if (ok) {
                puts1("OK - H:"); putu8(humidity);
                puts1("% T:"); putu8(temperature); puts1("C\r\n");
                current_state = STATE_READ_COLOR;
            } else {
                puts1("FAILED - Retrying in 3s\r\n");
                dly(3000000);
            }



            break;

        case STATE_READ_COLOR:
            puts1("Reading color... ");
            tcs3200_measure(&red_freq, &green_freq, &blue_freq);

            if(red_freq || green_freq || blue_freq) {
                puts1("OK - R:"); putu32(red_freq);
                puts1(" G:"); putu32(green_freq);
                puts1(" B:"); putu32(blue_freq); puts1(" Hz\r\n");
                current_state = STATE_DECIDE_BASKET;
            } else {
                puts1("FAILED - No color data\r\n");
                current_state = STATE_ERROR;
            }
            break;

        case STATE_DECIDE_BASKET:
            target_basket = classify_clothing(humidity, red_freq, green_freq, blue_freq);

            puts1("Classification: ");
            switch(target_basket) {
                case BASKET_DRY_LIGHT:
                    puts1("DRY LIGHT clothing");
                    break;
                case BASKET_DRY_DARK:
                    puts1("DRY DARK clothing");
                    break;
                case BASKET_DAMP_LIGHT:
                    puts1("DAMP LIGHT clothing");
                    break;
                case BASKET_DAMP_DARK:
                    puts1("DAMP DARK clothing");
                    break;
                default:
                    puts1("UNKNOWN - check sensors");
                    break;
            }
            puts1("\r\n");

            current_state = STATE_ACTUATE;
            break;

        case STATE_ACTUATE:
            // This is where you'd trigger the servos/actuators
            // For now, just output which basket to use
            puts1("ACTION: Move to basket ");
            putu8(target_basket);
            puts1("\r\n");

            puts1("=== Measurement Complete ===\r\n\r\n");
            dly(3000000); // Wait 3 seconds before next measurement
            current_state = STATE_IDLE;
            break;

        case STATE_ERROR:
            puts1("SYSTEM ERROR - Resetting in 3 seconds...\r\n");
            dly(3000000);
            current_state = STATE_IDLE;
            break;
    }
}

int main(void) {
    WDTCTL = WDTPW | WDTHOLD;
    PM5CTL0 &= ~LOCKLPM5;

    // System initialization
    clock_1mhz();
    uart1_init_9600();

    // Sensor initialization
    dht11_init();
    tcs3200_init();

    // Enable interrupts (for TCS3200)
    __enable_interrupt();

    puts1("\r\nLaundry Sorter System Initialized\r\n");
    puts1("DHT11 + TCS3200 Integrated State Machine\r\n");
    puts1("Waiting 2 seconds for sensors to stabilize...\r\n");
    dly(2000000);

    while(1) {
        run_state_machine();
        dly(50000); // Small delay between state checks
    }
}
