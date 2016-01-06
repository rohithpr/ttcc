import re

DEVICES = {}

def register(device_name, device_details):
    global DEVICES

    # Overwrite or ignore a duplicate registration?
    # Check if the device details is in the correct format
    # Check if type is an object of a subclass of TypeBaseClass
    
def parse_device(sentence):
    global DEVICES
    words = sentence.split()
    target_device = []

    target_device = list(set(words)&set(DEVICES.keys()))
    for device in DEVICES:
            device_alias = list(set(words) & set(DEVICES[device]['alias']))
            target_device.extend(device_alias)
    return target_device
         

def parse_intent(sentence, device):
    intent = []
    global DEVICES
    operations = list(DEVICES[device]['operations'].keys())

    for operation in operations:
        for trigger in DEVICES[device]['operations'][operation]['triggers']:
            if re.search(trigger, sentence):
                intent.append(operation)
    return intent

def parse_args(sentence, device, intent, operation):
    pass

def parse(sentence):
    devices = []
    devices = parse_device(sentence)    #devices contains a list of matches devices from the sentence
    if not devices:
        print("No device found")
    else:
        for device in devices:          #individual device
            intents = []
            intents = parse_intent(sentence, device)    #single device can have multiple intents

            if not intents:
                print("No intents for ",device," found")
            else:
                for intent in intents:      #individual intent
                    argument_values = parse_args(sentence, device, intent)

                    response = {
                        'device': device,
                        'intent': intent,
                        'arguments': argument_values
                    }
                    return response
