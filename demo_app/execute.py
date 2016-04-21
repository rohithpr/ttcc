from TwitterAPI import TwitterAPI
import datetime
import os
import re
import config
import requests
import time
from mutagen.mp3 import MP3

path = os.path.expanduser('~/')
city = 'bangalore' # the default city to check on weather in bangalore

consumer_key = config.twitter['consumer_key']
consumer_secret = config.twitter['consumer_secret']
access_token_secret = config.twitter['access_token_secret']
access_token_key = config.twitter['access_token_key']

appid = config.weather_appid

# Function called when the file/folder names generated by os.walk are being compared with the input text -- for totem and file explorer
def name_matcher(text, filename):
    if text == filename:
        return True
    li = text.split()
    if filename.endswith(('.mp3','.MP3','.mp4','.m3u','.m4a','.wav','.flv')):
        filename = filename[:-4]
    fn_list_words = re.split(' |-|_|\.', filename.lower())
    for word in li:
        if word.lower() in fn_list_words:
            fn_list_words.pop(fn_list_words.index(word.lower()))
        else:
            return False
    return True

def kelvin2celsius(temp):
    return temp - 273

def totem(command, device, output):
    cl = 'totem ' + command['intent']
    if command['intent'] == '--play':
        print(command)
        for alias in device['alias']:
            command['arguments']['name'] = command['arguments']['name'].replace(alias, 'totem')

        # Remove 'totem' and 'in','with','using' if it exists in the filname
        if ('totem') in command['arguments']['name']:
            temp = command['arguments']['name'].split(' ')
            temp.remove('totem')
            if temp[len(temp)-1] in ['in','with','using']:
                del temp[len(temp)-1]
            command['arguments']['name'] = ' '.join(temp)

        #Only `totem --play` will unpause the application
        # If the name of a song is mentioned `totem --play songname` will be executed
        if command['arguments']['name']:
            command['arguments']['name'] = command['arguments']['name'].strip(' ')
            matched_files = [] # Keep track of all the files that match

            # Walk in the required directories to find music
            for dirName, subdirList, fileList in os.walk("./"):
                for filename in fileList:
                    if name_matcher(command['arguments']['name'], filename):
                        matched_files.append(filename)
            if len(matched_files) == 0:
                output['message'] = 'No files were found'
                return output
            elif len(matched_files) > 1:
                output['final'] = False
                output['message'] = 'Which song do you want to play?'
                output['options'] = matched_files
                output['type'] = 'option'
                output['option-type'] = 'arguments' # Refer JSON to know what this refers to
                output['option-name'] = 'name' # Refer JSON to know what this refers to
                return output
            else:
                song_details = MP3(matched_files[0])
                duration = round(song_details.info.length + 3, 3) * 1000
                output = {
                    'commands': [],
                    'error': False,
                    'final': True,
                    'parsed': command,
                    'message': 'Executed command',
                    'type': None,
                    'duration': duration
                }
                cl += ' "' + matched_files[0] + '"'
    cl += ' &'
    return_value = os.system(cl)
    if return_value == 0:
        return output
    # What should we do if return value isn't 0?
    return output

def tweet(command, device, output):
    tweets = []
    others = True # used to differentitae trending tweets from others

    try:
        api = TwitterAPI(consumer_key, consumer_secret, access_token_key, access_token_secret)
        obj = command['arguments']['name']
        if command['intent'] == 'trends/place':
            others = False
            res = api.request('trends/available') # to find the what on earth id 'an id for a particular place'
            for i in res:
                if i['country'].lower() == command['arguments']['name'][1:]:
                    woeid = i['woeid']
            response = api.request(command['intent'], {'id':woeid}) # you only get links to trending news in twitter
            count = 0 # specifies no of tweets for places 'currently  5'
            for item in response:
                count += 1
                if not re.match('[a-zA-Z0-9]',item['query'][0]):
                    ret_query = item['query'][3:]
                else:
                    ret_query = item['query']
                tweets.append(ret_query + '<br />       ' + str(item['url'])) # change the output format as required
                if count == 5:
                    break

        elif command['intent'] == 'statuses/user_timeline':
            query = 'screen_name'

        else:
            query = 'q'

        if others == True: # if the request is not on trending news
            response = api.request(command['intent'], {query:obj, 'count':5})

            for item in response:
                string = item['text'].replace('\n', '<br />')
                tweets.append(string)
        # FOR MAKING HREF LINKS
        no_of_tweets = len(tweets)
        for i in range(no_of_tweets):
            tweet_length = len(tweets[i])
            while 1:
                first_char = 0
                index = tweets[i].find('http', first_char, tweet_length)
                if index == -1:
                    break
                m = index # 'm' to find the end of https
                while tweets[i][m]!=' ' and m < (tweet_length-1):
                    m += 1
                if m < tweet_length:
                    text = tweets[i][index:m+1]
                    tweets[i] = tweets[i].replace(text, 'replace')
                    first_char = m
                    tweet_length = len(tweets[i])

            replace_index = tweets[i].find('replace')
            if replace_index != -1:
                blank = '_blank'
                replace = '<a href = '+text+' target = '+blank+'>'+text+'</a> '
                tweets[i] = tweets[i].replace('replace', replace)

        output = {
             'commands': [],
             'error': False,
             'final': True,
             'parsed': command,
             'message': 'Executed command',
             'type': None,
             'tweet': tweets
        }
        return output
    except:
        output = {
            'message': 'Invalid input',
            'error':True,
            'final':True
        }
        return output

# example: forecast set city 'cityname'
# 2. forecast will it rain tomorrow
# 3. forecast what will be the weather tomorrow
# 4. forecast do i need an umbrella tomorrow
# 5. forecast reset city ... by default it's bangalore
# etc...
# the output displayed should be made proper
def weather(command, device, output):
    global city
    weather_report = []
    info = []
    try:
        if command['intent'] == 'set city':
            city = command['arguments']['name']
            city = city[1:len(city)] # to remove the space, which is the first character
            output['final'] = False
            output['message'] = 'now ask what you want'
            return output

        if command['intent'] == 'reset':
            city ='bangalore'
            output['final'] = False
            output['message'] = 'now ask what you want'
            return output
        input_array = output['input'].split()
        if 'today' in input_array:
            day = 0 # day == 0 represents today
        elif 'tomorrow' in input_array:
            day = 1
        elif 'yesterday' in input_array: # when input is on yesterday's weather, should be handled later
            day =0
        elif 'week' in input_array:
            day = 6
        else:
            day = 0

        # below line is used to get weather report history
        # res = requests.get('http://api.openweathermap.org/data/2.5/history/city?q=Bangalore,IN&type=hour')
        response = requests.get('http://api.openweathermap.org/data/2.5/forecast/daily?q='+city+'&APPID='+appid)
        result = response.json()
        epoc_time = result['list'][day]['dt'] # time is in epoch format
        date_time = time.gmtime(epoc_time) # convert UNIX time representation to date time
        info.append(result['city']['name'])
        info.append('Date : '+str(' '.join(str(e) for e in date_time[0:3]))) # getting only year, month, and day
        if command['intent'] == 'minTemperature':
            weather_report.append('Minimum Temperature is '+str(round(kelvin2celsius(result['list'][day]['temp']['min']), 2)))
        elif command['intent'] == 'maxTemperature':
            weather_report.append('Maximum Temperature is '+str(round(kelvin2celsius(result['list'][day]['temp']['max']), 2)))
        elif command['intent'] == 'will': # ex: will it rain tomorrow
            if 'rain' in input_array:
                if 'rain' in result['list'][day].keys():
                    weather_report.append('Yes it rains today')
                    weather_report.append('Rain upto '+str(result['list'][day]['rain']) + ' millimetres is expected')
                else:
                    weather_report.append('no rain')
            elif 'sunny' in input_array:
                if result['list'][day]['temp']['max'] > 303:
                    weather_report.append('yes its sunny, you may even need umbrella')
                else:
                    weather_report.append('No')
            else:
                if result['list'][day]['weather'][0]['main'] == 'Clouds': # need to check on 'main' in returned json
                    weather_report.append('Yes its cloudy')
                    weather_report.append(result['list'][day]['weather'][0]['description'])
                else:
                    weather_report.append('Not cloudy')

        elif command['intent'] == 'humidity':
            weather_report.append(result['list'][day]['humidity'])
        elif command['intent'] == 'windspeed':
            weather_report.append(result['list'][day]['speed'])
        elif command['intent'] == 'need': # ex: do i need an umbrella,
            if 'rain' in result['list'][day].keys(): # need one when it is raining
                weather_report.append('Yes, you need an umbrella')
                weather_report.append('Rain upto '+str(result['list'][day]['rain']) + ' millimetres is expected')
            elif round(kelvin2celsius(result['list'][day]['temp']['max']), 2) > 30.00: # need one when its hot
                weather_report.append('Yes you need an umbrella')
                weather_report.append('Maximum Temperature is about '+str(round(kelvin2celsius(result['list'][day]['temp']['max']), 2)) + ' celcius')
            else:weather_report.append('No')

        elif command['intent'] == 'weather':
            weather_report.append('Humidity : '+str(result['list'][day]['humidity']))
            weather_report.append('Wind Speed : '+str(result['list'][day]['speed']))
            weather_report.append('Minimum Temperature : '+str(round(kelvin2celsius(result['list'][day]['temp']['min']), 2))+ ' celcius')
            weather_report.append('Maximum Temperature : '+str(round(kelvin2celsius(result['list'][day]['temp']['max']), 2)) + ' celcius')
            weather_report.append('Day Temperature : '+str(round(kelvin2celsius(result['list'][day]['temp']['day']), 2)) + ' celcius')
            weather_report.append('Evening Temperature : '+str(round(kelvin2celsius(result['list'][day]['temp']['eve']), 2)) + ' celcius')
            weather_report.append('Morning Temperature : '+str(round(kelvin2celsius(result['list'][day]['temp']['morn']), 2)) + ' celcius')
            if 'rain' in result['list'][day].keys():
                weather_report.append('Rain upto '+str(result['list'][day]['rain']) + ' millimetres is expected')

        # s = datetime.datetime(2016,4,15,0,0).timestamp()
        # e = datetime.datetime(2016,4,16,0,0).timestamp()

        output = {
                 'commands': [],
                 'error': False,
                 'final': True,
                 'parsed': command,
                 'message': 'Executed command',
                 'type': None,
                 'info': info,
                 'weather': weather_report
            }
        return output
    except:
        output = {
            'message': 'invalid input',
            'error':True,
            'final':True
        }
        return output

def file_explorer(command, device, output):
    global path
    if command['intent'] == '--current-path':
        output = {
            'commands': [],
            'error': False,
            'final': True,
            'parsed': command,
            'message': 'Executed command',
            'type': None,
            'path': path
        }
        return output

    if command['intent'] == '--goto':
        home_folders = ['desktop','documents','music','pictures','videos','public','templates']
        if command['arguments']['name']:
            command['arguments']['name'] = command['arguments']['name'].strip(' ')
        if command['arguments']['name'] == 'home':
            path = os.path.expanduser('~/')
            path = path[:-1] # This has been done because when 'move up' is said it removes the directory before the last slash.

        elif command['arguments']['name'] in home_folders:
            temp_path = '~/' + command['arguments']['name'].title() # /home/username/music becomes /home/username/Music
            path = os.path.expanduser(temp_path)
        output = {
            'commands': [],
            'error': False,
            'final': True,
            'parsed': command,
            'message': 'Executed command',
            'type': None,
            'path': path
        }
        return output

    if command['intent'] == '--reset-path':
        path = os.path.expanduser('~/')
        output = {
            'commands': [],
            'error': False,
            'final': True,
            'parsed': command,
            'message': 'Path has been reset',
            'type': None,
            'path': path
        }
        return output

    if command['intent'] == '--display':
        for dir_name, subdir_list, file_list in os.walk(path):
            files = [f for f in file_list if not f[0] == '.'] # f and d are just temporary variables in order to check if it is a hidden file/directory or not
            directories = [d for d in subdir_list if not d[0] == '.']
            break
        output = {
            'commands': [],
            'error': False,
            'final': True,
            'parsed': command,
            'message': ' Directories and Files ',
            'path': path,
            'option_dir': directories,
            'option_files': files
        }
        return output

    if command['intent'] == '--display-dir':
        for dir_name, subdir_list, file_list in os.walk(path):
            directories = [d for d in subdir_list if not d[0] == '.']
            break
        output = {
            'commands': [],
            'error': False,
            'final': True,
            'parsed': command,
            'message': ' Directories ',
            'path': path,
            'option_dir': directories,
        }
        return output

    if command['intent'] == '--display-files':
        for dir_name, subdir_list, file_list in os.walk(path):
            files = [f for f in file_list if not f[0] == '.']
            break
        output = {
            'commands': [],
            'error': False,
            'final': True,
            'parsed': command,
            'message': ' Files ',
            'path': path,
            'option_files': files
        }
        return output
    if command['intent'] == '--hidden':
        for dir_name, subdir_list, file_list in os.walk(path):
            files = [f for f in file_list if f[0] == '.']
            directories = [d for d in subdir_list if d[0] == '.']
            break
        output = {
            'commands': [],
            'error': False,
            'final': True,
            'parsed': command,
            'message': ' Hidden directories and Files ',
            'path': path,
            'option_dir': directories,
            'option_files': files
        }
        return output

    if command['intent'] == '--hidden-dir':
        for dir_name, subdir_list, file_list in os.walk(path):
            directories = [d for d in subdir_list if d[0] == '.']
            break
        output = {
            'commands': [],
            'error': False,
            'final': True,
            'parsed': command,
            'message': ' Hidden directories ',
            'path': path,
            'option_dir': directories,
        }
        return output
    if command['intent'] == '--hidden-files':
        for dir_name, subdir_list, file_list in os.walk(path):
            files = [f for f in file_list if f[0] == '.']
            break
        output = {
            'commands': [],
            'error': False,
            'final': True,
            'parsed': command,
            'message': ' Hidden files ',
            'path': path,
            'option_files': files
        }
        return output

    if command['intent'] == '--move-up':
        path = os.path.dirname(path) # Return the directory name of pathname
        output = {
            'commands': [],
            'error': False,
            'final': True,
            'parsed': command,
            'message': 'Executed command',
            'type': None,
            'path': path
        }
        return output

    if command['intent'] == '--step-into':
        if command['arguments']['name']:
            command['arguments']['name'] = command['arguments']['name'].strip(' ')
        for dir_name, subdir_list, file_list in os.walk(path):
            for sub_dir in subdir_list:
                if name_matcher(command['arguments']['name'], sub_dir):
                    path = path + '/' + sub_dir
                    output = {
                        'commands': [],
                        'error': False,
                        'final': True,
                        'parsed': command,
                        'message': 'Path changed',
                        'type': None,
                        'path': path
                    }
                    return output
            break
        output = {
            'commands': [],
            'error': False,
            'final': True,
            'parsed': command,
            'message': 'Specified sub-directory does not exist. Path unchanged',
            'type': None,
            'path': path
        }
        return output

def tetris(command, device, output):
    return output

def soundcloud(command, device, output):
    return output

def process(command, device, output):
    if command['device'] == 'totem':
        return totem(command, device, output)
    if command['device'] == 'tweet':
        return tweet(command, device, output)
    if command['device'] == 'soundcloud':
        return soundcloud(command, device, output)
    if command['device'] == 'file_explorer':
        return file_explorer(command, device, output)
    if command['device'] == 'weather':
        return weather(command, device, output)
    elif command['device'] == 'tetris':
        return tetris(command, device, output)
