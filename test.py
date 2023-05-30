barcode_input = input("Enter barcode here: ")
device_type, device_id, identifier = barcode_input.split('-')
print(device_type)
print(device_id)
print(identifier)

barcode_input = input("Enter barcode here: ")
barcode_input = barcode_input[:-9]  
device_type, device_id = barcode_input.split('-')
print(device_type)
print(device_id)