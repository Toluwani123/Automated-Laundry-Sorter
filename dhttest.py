import time
import adafruit_dht
import board


SENSOR = adafruit_dht.DHT22(board.D23)





def main():
	
	print("Testing dht")
	
	
	while True:
		try:
			t = SENSOR.temperature
			h = SENSOR.humidity
			
			
				
			print(t,h)
				
				
			
		except Exception as e:
			
			print(e)
			
			
		time.sleep(2)
		
		
if __name__ == "__main__":
	try:
		main()
		
	except KeyboardInterrupt:
		
		print("End")
