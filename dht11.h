#ifndef DHT11_H
#define DHT11_H
#define DHT_BIT BIT3

void dht11_init(void);
char dht11_read(unsigned char *humidity, unsigned char *temperature);


#endif
