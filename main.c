#include <msp430.h>
#include "dht11.h"
#include "tcs3200.h"
#include <stdint.h>

#define dly(cyc) __delay_cycles(cyc)

#define HUMIDITY_THRESHOLD 70    // % above which clothing is considered damp
#define V_THRESHOLD 0.40f

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
static float gH = 0.0f, gS = 0.0f, gV = 0.0f;
static const char* gColor = "unknown";
static unsigned char humidity = 0;
static unsigned char temperature = 0;
static unsigned long red_freq = 0, green_freq = 0, blue_freq = 0;
static basket_t target_basket = BASKET_UNKNOWN;

/* ---- Two-point calibration (replace with your measured values) ----
   Put sensor on matte BLACK cloth -> record (R0,G0,B0)
   Put sensor on matte WHITE card  -> record (R1,G1,B1)
   Paste them below.
*/
static unsigned long CAL_BLACK[3] = {  3900,   3900,   4500 };   // R0,G0,B0 (example)
static unsigned long CAL_WHITE[3] = {  9600,   9305,  10800 };   // R1,G1,B1 (example)

static void normalize_rgb(unsigned long fr, unsigned long fg, unsigned long fb,
                          float *R, float *G, float *B)
{
    unsigned long r0 = CAL_BLACK[0], g0 = CAL_BLACK[1], b0 = CAL_BLACK[2];
    unsigned long r1 = CAL_WHITE[0], g1 = CAL_WHITE[1], b1 = CAL_WHITE[2];
    float rn, gn, bn;
    unsigned long r_span, g_span, b_span;

    // Calculate spans with protection against division by zero
    r_span = (r1 > r0) ? (r1 - r0) : 1;
    g_span = (g1 > g0) ? (g1 - g0) : 1;
    b_span = (b1 > b0) ? (b1 - b0) : 1;

    // subtract black, divide by span; clamp to [0,1]
    rn = (float)((fr > r0) ? (fr - r0) : 0) / (float)r_span;
    gn = (float)((fg > g0) ? (fg - g0) : 0) / (float)g_span;
    bn = (float)((fb > b0) ? (fb - b0) : 0) / (float)b_span;

    if (rn < 0) rn = 0;
    if (rn > 1) rn = 1;
    if (gn < 0) gn = 0;
    if (gn > 1) gn = 1;
    if (bn < 0) bn = 0;
    if (bn > 1) bn = 1;

    *R = rn;
    *G = gn;
    *B = bn;
}

/* HSV helpers from normalized RGB (no lib math needed) */
static float max3(float a, float b, float c)
{
    float m = a;
    if (b > m) m = b;
    if (c > m) m = c;
    return m;
}

static float min3(float a, float b, float c)
{
    float m = a;
    if (b < m) m = b;
    if (c < m) m = c;
    return m;
}

static float rgb_to_hsv(float R, float G, float B, float *S_out, float *V_out){
    float maxv = max3(R, G, B);
    float minv = min3(R, G, B);
    float delta = maxv - minv;
    float H = 0.0f;

    *V_out = maxv;
    *S_out = (maxv > 0.0f) ? (delta / maxv) : 0.0f;

    if (delta == 0.0f)
        return 0.0f;          // gray → hue 0 by convention

    if (maxv == R) {
        H = 60.0f * ((G - B) / delta);
    } else if (maxv == G) {
        H = 60.0f * ((B - R) / delta + 2.0f);
    } else {
        H = 60.0f * ((R - G) / delta + 4.0f);
    }

    if (H < 0.0f)
        H += 360.0f;

    return H;
}

/* --- replace your name_from_hsv signature with this (body unchanged) --- */
static const char* name_from_hsv(float H, float S_in, float V_in)
{
    if (V_in < 0.15f)
        return "black";
    if (S_in < 0.12f)
        return (V_in > 0.70f) ? "white" : "gray";
    if (H <  15.0f || H >= 345.0f)
        return "red";
    if (H <  45.0f)
        return "orange";
    if (H <  70.0f)
        return "yellow";
    if (H < 170.0f)
        return "green";
    if (H < 200.0f)
        return "cyan";
    if (H < 255.0f)
        return "blue";
    if (H < 290.0f)
        return "purple";
    return "magenta";
}

/* --- replace your classify_clothing signature & first lines with this --- */
basket_t classify_clothing(unsigned char hum, float V_in)
{
    const int is_damp = (hum >= HUMIDITY_THRESHOLD);
    const int is_dark = (V_in <= V_THRESHOLD);

    if (is_damp) {
        return is_dark ? BASKET_DAMP_DARK : BASKET_DAMP_LIGHT;
    } else {
        return is_dark ? BASKET_DRY_DARK : BASKET_DRY_LIGHT;
    }
}

// Thresholds - adjust based on your testing
#define HUMIDITY_THRESHOLD 70    // % above which clothing is considered damp
#define V_THRESHOLD 0.40f        // Value threshold for dark/light classification

/* UART Functions */
static void uart1_init_9600(void)
{
    P3SEL1 &= ~(BIT4|BIT5);
    P3SEL0 |= (BIT4|BIT5);
    UCA1CTLW0 = UCSWRST | UCSSEL__SMCLK;
    UCA1BRW   = 6;
    UCA1MCTLW = UCOS16 | (8<<4) | (0x20<<8);
    UCA1CTLW0 &= ~UCSWRST;
}

static void putc1(char c)
{
    while(!(UCA1IFG & UCTXIFG));
    UCA1TXBUF = c;
}

static void puts1(const char *s)
{
    while(*s) putc1(*s++);
}

static void putu8(unsigned char v)
{
    char b[4];
    unsigned int i = 3;
    b[i] = 0;
    do {
        b[--i] = '0' + (v % 10);
        v /= 10;
    } while(v);
    puts1(&b[i]);
}

static void putu32(unsigned long v)
{
    char b[11];
    unsigned int i = 10;
    b[i] = 0;
    do {
        b[--i] = '0' + (v % 10);
        v /= 10;
    } while(v);
    puts1(&b[i]);
}

/* 1 MHz clock */
static void clock_1mhz(void)
{
    CSCTL0_H = CSKEY_H;
    CSCTL1 = DCOFSEL_0;
    CSCTL2 = SELA__VLOCLK | SELS__DCOCLK | SELM__DCOCLK;
    CSCTL3 = DIVA__1 | DIVS__1 | DIVM__1;
    CSCTL0_H = 0;
}

/* Classification Logic */


/* State Machine */
void run_state_machine(void)
{
    switch(current_state)
    {
        case STATE_IDLE:
            puts1("\r\n=== Starting Measurement ===\r\n");
            current_state = STATE_READ_HUMIDITY;
            break;

        case STATE_READ_HUMIDITY:
        {
            uint8_t saved_p1ie;
            char ok;

            puts1("Reading humidity... ");

            // Reset DHT11 pin
            P1DIR &= ~DHT_BIT;
            P1REN |= DHT_BIT;
            P1OUT |= DHT_BIT;
            dly(100000); // 100ms stabilization

            /* --- pause TCS3200 interrupt during DHT transaction --- */
            saved_p1ie = P1IE;                // save Port 1 interrupt enable state
            P1IE &= ~TCS_OUT_PIN;             // mask TCS3200 OUT interrupt
            __disable_interrupt();            // avoid preemption during tight DHT timing

            ok = dht11_read(&humidity, &temperature);

            __enable_interrupt();
            P1IFG &= ~TCS_OUT_PIN;            // clear any pending edge captured while masked
            P1IE = saved_p1ie;                // restore Port 1 interrupt enables
            /* ------------------------------------------------------ */

            if (ok) {
                puts1("OK - H:");
                putu8(humidity);
                puts1("% T:");
                putu8(temperature);
                puts1("C\r\n");
                current_state = STATE_READ_COLOR;
            } else {
                puts1("FAILED - Retrying in 3s\r\n");
                dly(3000000);
            }
            break;
        }

        case STATE_READ_COLOR:
        {
            float Rn, Gn, Bn;
            float S_out, V_out, H;
            const char* color;

            puts1("Reading color... ");
            tcs3200_measure(&red_freq, &green_freq, &blue_freq);

            if(red_freq || green_freq || blue_freq)
            {
                normalize_rgb(red_freq, green_freq, blue_freq, &Rn, &Gn, &Bn);
                H = rgb_to_hsv(Rn, Gn, Bn, &S_out, &V_out);
                color = name_from_hsv(H, S_out, V_out);

                // persist for next state
                gH = H;
                gS = S_out;
                gV = V_out;
                gColor = color;

                // Debug prints
                puts1(" NormRGB=");
                putu32((unsigned long)(Rn * 1000));
                puts1(",");
                putu32((unsigned long)(Gn * 1000));
                puts1(",");
                putu32((unsigned long)(Bn * 1000));
                puts1(" HSV=(");
                putu32((unsigned long)H);
                puts1("deg, ");
                putu32((unsigned long)(S_out * 100));
                puts1("%, ");
                putu32((unsigned long)(V_out * 100));
                puts1("%) -> ");
                puts1(color);
                puts1("\r\n");

                puts1("OK - R:");
                putu32(red_freq);
                puts1(" G:");
                putu32(green_freq);
                puts1(" B:");
                putu32(blue_freq);
                puts1(" Hz\r\n");
                current_state = STATE_DECIDE_BASKET;
            } else {
                puts1("FAILED - No color data\r\n");
                current_state = STATE_ERROR;
            }
            break;
        }

        case STATE_DECIDE_BASKET:
            target_basket = classify_clothing(humidity, gV);

            puts1("Classification: ");
            switch(target_basket)
            {
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

int main(void)
{
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

    while(1)
    {
        run_state_machine();
        dly(50000); // Small delay between state checks
    }
}
