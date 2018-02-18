import serial
import time
import requests

def serial_in(resp_port, ard_port):
	ser_resp = serial.Serial(resp_port, 9600, timeout=2)
	ser_ard = serial.Serial(ard_port, 9600, timeout=2)
	ser_resp.write(b'c')
	print(ser_resp.readline(), '***')
	while True:
		line_resp = ser_resp.readline()
		line_ard = ser_ard.readline()
		line_ard = str(line_ard, 'utf-8').replace('\r', '').replace('\n', '')
		cur_time = time.time()
		query_resp = line_to_query(str(line_resp, 'utf-8'), cur_time)
		tok_ard = line_ard.split(' ')
		if tok_ard[0] == '':
			query_resp += '&carbonmonoxide=null&co2=null'
		else:
			query_resp += '&carbonmonoxide=' + tok_ard[0] + '&co2=' + tok_ard[1]
		print("https://air-quality-195519.appspot.com", query_resp)
		r = requests.get("https://air-quality-195519.appspot.com" + query_resp + '&location=null')
		# send to server here
		time.sleep(5)


def line_to_query(line, read_time):
	# SN, PPB, TEMP, RH, RawSensor, TempDigital, RHDigital, Day, Hour, Minute, Second
	# '110816030320, 107, 25, 21, 32598, 26884, 14454, 00, 00, 01, 49'	
	print(line == '')
	if line == '':
		return '?respiratoryirritants=null&datetime=' + str(read_time)
	tok = line.split(', ')
	'''
	dict = {'PPB' : 0, 'TEMP' : 0, 'RH' : 0, 'RawSensor' : 0, 'TempDigital' : 0, 'RHDigital' : 0, 'SecTime' : 0, 'DateTime' : ''}
	dict['PPB'] = tok[1]
	dict['TEMP'] = tok[2]
	dict['RH'] = tok[3]
	dict['RawSensor'] = tok[4]
	dict['TempDigital'] = tok[5]
	dict['RHDigital'] = tok[6]
	dict['SecTime'] = read_time
	dict['DateTime'] = time.ctime(read_time).replace(' ', '_')
	'''
	
	ppb = tok[1]
	sectime = read_time
	print('?respiratoryirritants=', str(ppb), '&datetime=', str(read_time), '*****')
	return '?respiratoryirritants=' + str(ppb) + '&datetime=' + str(read_time)
	'''
	for k, v in dict.items():
		query += k + '=' + str(v) + '&'
	return query[:-1]
	'''

def main():
	#print(line_to_query('110816030320, 107, 25, 21, 32598, 26884, 14454, 00, 00, 01, 49', time.time()))
	serial_in('/dev/ttyUSB0', '/dev/ttyACM0')
	#serial_in('/dev/cu.SLAB_USBtoUART', '/dev/cu.usbmodem1421')

if __name__ == '__main__':
	main()
